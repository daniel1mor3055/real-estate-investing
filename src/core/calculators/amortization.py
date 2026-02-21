"""Amortization schedule calculator with Israeli mortgage event engine."""

from typing import Dict, List, Optional
import pandas as pd
import numpy_financial as npf
from pydantic import BaseModel, Field

from .base import Calculator, CalculatorResult
from ..models.financing import (
    SubLoan,
    RepaymentMethod,
    GraceType,
    PrepaymentOption,
)


class AmortizationPayment(BaseModel):
    """Single payment in amortization schedule."""

    payment_number: int
    year: int
    month: int
    beginning_balance: float
    payment_amount: float
    principal_payment: float
    interest_payment: float
    ending_balance: float
    cumulative_principal: float
    cumulative_interest: float
    events: List[str] = Field(default_factory=list)


class AmortizationSchedule(BaseModel):
    """Complete amortization schedule."""

    loan_amount: float
    interest_rate: float
    loan_term_years: int
    monthly_payment: float
    total_interest_paid: float
    payments: List[AmortizationPayment]
    track_schedules: Dict[str, List[AmortizationPayment]] = Field(
        default_factory=dict
    )

    def to_dataframe(self) -> pd.DataFrame:
        """Convert schedule to pandas DataFrame."""
        return pd.DataFrame([p.dict() for p in self.payments])

    def get_yearly_summary(self) -> pd.DataFrame:
        """Get yearly summary of payments."""
        df = self.to_dataframe()
        yearly = (
            df.groupby("year")
            .agg(
                {
                    "payment_amount": "sum",
                    "principal_payment": "sum",
                    "interest_payment": "sum",
                    "ending_balance": "last",
                    "cumulative_principal": "last",
                    "cumulative_interest": "last",
                }
            )
            .round(2)
        )
        return yearly

    def get_track_dataframe(self, track_name: str) -> Optional[pd.DataFrame]:
        """Get a DataFrame for a specific track's schedule."""
        if track_name not in self.track_schedules:
            return None
        return pd.DataFrame(
            [p.dict() for p in self.track_schedules[track_name]]
        )


class AmortizationCalculator(Calculator):
    """Calculator for loan amortization schedules."""

    def calculate(self, **kwargs) -> CalculatorResult:
        """Calculate amortization schedule."""
        financing = self.deal.financing

        if financing.is_cash_purchase or financing.loan_amount == 0:
            return CalculatorResult(
                success=True,
                data=AmortizationSchedule(
                    loan_amount=0,
                    interest_rate=0,
                    loan_term_years=0,
                    monthly_payment=0,
                    total_interest_paid=0,
                    payments=[],
                ),
                warnings=["This is a cash purchase - no amortization schedule needed"],
            )

        if hasattr(financing, "sub_loans") and financing.sub_loans:
            return self._calculate_israeli_mortgage_schedule(financing)
        else:
            if financing.interest_rate is None:
                return CalculatorResult(
                    success=False,
                    errors=["Interest rate is not set for this financing"],
                )

            schedule = self._calculate_simple_schedule(
                financing.loan_amount,
                financing.interest_rate / 100,
                financing.loan_term_years,
            )

            return CalculatorResult(success=True, data=schedule)

    def _calculate_simple_schedule(
        self, loan_amount: float, annual_rate: float, years: int
    ) -> AmortizationSchedule:
        """Calculate amortization schedule for a simple single loan (legacy)."""
        monthly_rate = annual_rate / 12
        num_payments = years * 12

        if monthly_rate > 0:
            monthly_payment = float(npf.pmt(monthly_rate, num_payments, -loan_amount))
        else:
            monthly_payment = loan_amount / num_payments

        payments = []
        balance = loan_amount
        cumulative_principal = 0
        cumulative_interest = 0

        for i in range(1, num_payments + 1):
            interest = balance * monthly_rate
            principal = monthly_payment - interest

            if balance < principal:
                principal = balance
                monthly_payment = principal + interest

            balance -= principal
            cumulative_principal += principal
            cumulative_interest += interest

            payment = AmortizationPayment(
                payment_number=i,
                year=(i - 1) // 12 + 1,
                month=(i - 1) % 12 + 1,
                beginning_balance=balance + principal,
                payment_amount=monthly_payment,
                principal_payment=principal,
                interest_payment=interest,
                ending_balance=max(0, balance),
                cumulative_principal=cumulative_principal,
                cumulative_interest=cumulative_interest,
            )

            payments.append(payment)

            if balance <= 0:
                break

        total_interest = cumulative_interest

        return AmortizationSchedule(
            loan_amount=loan_amount,
            interest_rate=annual_rate * 100,
            loan_term_years=years,
            monthly_payment=monthly_payment,
            total_interest_paid=total_interest,
            payments=payments,
        )

    @staticmethod
    def generate_track_schedule(sub_loan: SubLoan) -> List[AmortizationPayment]:
        """Generate month-by-month amortization for a single track.

        Handles all advanced features: repayment methods (Spitzer/Equal/Bullet),
        grace periods, CPI indexation, dynamic rate changes, and prepayments.
        """
        if sub_loan.loan_amount <= 0:
            return []

        method = sub_loan.repayment_method
        effective_rate_pct = sub_loan.calculate_effective_rate()
        term_months = sub_loan.loan_term_months
        grace = sub_loan.grace_period
        rate_changes = sorted(sub_loan.rate_changes, key=lambda rc: rc.month)
        prepayments = sorted(sub_loan.prepayments, key=lambda pp: pp.month)

        current_rate = effective_rate_pct / 100.0
        current_monthly_rate = current_rate / 12.0

        index_rate_pct = (
            sub_loan.expected_cpi
            if sub_loan.track_type.is_cpi_linked and sub_loan.expected_cpi
            else 0.0
        )
        monthly_inflation = (
            (1 + index_rate_pct / 100.0) ** (1.0 / 12.0) - 1.0
            if index_rate_pct
            else 0.0
        )

        balance = sub_loan.loan_amount
        grace_months = grace.duration_months if grace else 0
        grace_ended = grace is None or grace_months == 0

        fixed_payment: Optional[float] = None
        principal_installment: Optional[float] = None

        if grace_ended:
            if method == RepaymentMethod.SPITZER:
                fixed_payment = float(
                    -npf.pmt(current_monthly_rate, term_months, balance)
                )
            elif method == RepaymentMethod.EQUAL_PRINCIPAL:
                principal_installment = balance / term_months

        schedule: List[AmortizationPayment] = []
        cumulative_principal = 0.0
        cumulative_interest = 0.0

        for m in range(1, term_months + 1):
            events: List[str] = []
            beginning_balance = balance

            # --- Rate changes at this month ---
            for rc in rate_changes:
                if rc.month == m:
                    current_rate += rc.delta / 100.0
                    current_monthly_rate = current_rate / 12.0
                    if grace_ended and method == RepaymentMethod.SPITZER:
                        remaining = term_months - (m - 1)
                        if remaining > 0 and current_monthly_rate > 0:
                            fixed_payment = float(
                                -npf.pmt(current_monthly_rate, remaining, balance)
                            )
                    events.append(
                        f"rate_change: {'+' if rc.delta >= 0 else ''}{rc.delta}%"
                    )

            # --- Grace: full deferral ---
            if (
                grace
                and grace.grace_type == GraceType.FULL_DEFERRAL
                and m <= grace_months
            ):
                if monthly_inflation:
                    balance *= 1 + monthly_inflation
                interest = balance * current_monthly_rate
                balance += interest
                payment = 0.0
                principal_paid = 0.0
                if not events:
                    events.append("grace:full_deferral")

            # --- Grace: interest only ---
            elif (
                grace
                and grace.grace_type == GraceType.INTEREST_ONLY
                and m <= grace_months
            ):
                if monthly_inflation:
                    balance *= 1 + monthly_inflation
                interest = balance * current_monthly_rate
                payment = interest
                principal_paid = 0.0
                if not events:
                    events.append("grace:interest_only")

            # --- Normal amortization ---
            else:
                # Re-amortize after grace ends
                if not grace_ended and m == grace_months + 1:
                    grace_ended = True
                    remaining = term_months - grace_months
                    if method == RepaymentMethod.SPITZER:
                        fixed_payment = float(
                            -npf.pmt(current_monthly_rate, remaining, balance)
                        )
                    elif method == RepaymentMethod.EQUAL_PRINCIPAL:
                        principal_installment = balance / remaining
                    events.append("grace_end")

                # CPI indexation before payment
                if monthly_inflation:
                    balance *= 1 + monthly_inflation
                    remaining = term_months - (m - 1)
                    if remaining > 0:
                        if method == RepaymentMethod.SPITZER:
                            fixed_payment = float(
                                -npf.pmt(current_monthly_rate, remaining, balance)
                            )
                        elif method == RepaymentMethod.EQUAL_PRINCIPAL:
                            principal_installment = balance / remaining

                # Payment calculation per method
                if method == RepaymentMethod.SPITZER:
                    interest = balance * current_monthly_rate
                    payment = float(fixed_payment)  # type: ignore[arg-type]
                    principal_paid = payment - interest
                    principal_paid = max(principal_paid, 0.0)
                    if principal_paid > balance:
                        principal_paid = balance
                        payment = principal_paid + interest
                    balance -= principal_paid

                elif method == RepaymentMethod.EQUAL_PRINCIPAL:
                    interest = balance * current_monthly_rate
                    principal_paid = float(principal_installment)  # type: ignore[arg-type]
                    if principal_paid > balance:
                        principal_paid = balance
                    payment = interest + principal_paid
                    balance -= principal_paid

                elif method == RepaymentMethod.BULLET:
                    interest = balance * current_monthly_rate
                    if m < term_months:
                        payment = interest
                        principal_paid = 0.0
                    else:
                        payment = interest + balance
                        principal_paid = balance
                        balance = 0.0

                else:
                    raise ValueError(f"Unknown repayment method: {method}")

            # --- Prepayments ---
            for pp in prepayments:
                if pp.month == m:
                    extra = min(pp.amount, balance)
                    payment += extra
                    principal_paid += extra
                    balance -= extra

                    remaining = term_months - m
                    if remaining > 0 and pp.option == PrepaymentOption.REDUCE_PAYMENT:
                        if method == RepaymentMethod.SPITZER:
                            fixed_payment = float(
                                -npf.pmt(current_monthly_rate, remaining, balance)
                            )
                        elif method == RepaymentMethod.EQUAL_PRINCIPAL:
                            principal_installment = balance / remaining
                    # REDUCE_TERM: keep same payment, loan ends earlier naturally
                    events.append(
                        f"prepayment: {extra:,.0f} ({pp.option.value})"
                    )

            cumulative_principal += principal_paid
            cumulative_interest += interest

            schedule.append(
                AmortizationPayment(
                    payment_number=m,
                    year=(m - 1) // 12 + 1,
                    month=((m - 1) % 12) + 1,
                    beginning_balance=round(beginning_balance, 2),
                    payment_amount=round(payment, 2),
                    principal_payment=round(principal_paid, 2),
                    interest_payment=round(interest, 2),
                    ending_balance=round(max(balance, 0), 2),
                    cumulative_principal=round(cumulative_principal, 2),
                    cumulative_interest=round(cumulative_interest, 2),
                    events=events,
                )
            )

            if balance <= 0.01:
                break

        return schedule

    def _calculate_israeli_mortgage_schedule(self, financing) -> CalculatorResult:
        """Calculate amortization schedule for Israeli mortgage with multiple tracks."""
        try:
            track_schedules: Dict[str, List[AmortizationPayment]] = {}

            for sub_loan in financing.sub_loans:
                track_payments = self.generate_track_schedule(sub_loan)
                track_schedules[sub_loan.name] = track_payments

            # Build month→payment lookup per track
            track_payment_maps: Dict[str, Dict[int, AmortizationPayment]] = {
                name: {p.payment_number: p for p in payments}
                for name, payments in track_schedules.items()
            }

            max_month = max(
                max(p.payment_number for p in payments)
                for payments in track_schedules.values()
            ) if track_schedules else 0

            combined: List[AmortizationPayment] = []
            cumulative_principal = 0.0
            cumulative_interest = 0.0

            for month_num in range(1, max_month + 1):
                total_beginning = 0.0
                total_payment = 0.0
                total_principal = 0.0
                total_interest = 0.0
                total_ending = 0.0
                all_events: List[str] = []

                for track_name, pmap in track_payment_maps.items():
                    p = pmap.get(month_num)
                    if p:
                        total_beginning += p.beginning_balance
                        total_payment += p.payment_amount
                        total_principal += p.principal_payment
                        total_interest += p.interest_payment
                        total_ending += p.ending_balance
                        for e in p.events:
                            all_events.append(f"{track_name}: {e}")

                if total_payment > 0 or total_beginning > 0:
                    cumulative_principal += total_principal
                    cumulative_interest += total_interest

                    combined.append(
                        AmortizationPayment(
                            payment_number=month_num,
                            year=(month_num - 1) // 12 + 1,
                            month=((month_num - 1) % 12) + 1,
                            beginning_balance=round(total_beginning, 2),
                            payment_amount=round(total_payment, 2),
                            principal_payment=round(total_principal, 2),
                            interest_payment=round(total_interest, 2),
                            ending_balance=round(total_ending, 2),
                            cumulative_principal=round(cumulative_principal, 2),
                            cumulative_interest=round(cumulative_interest, 2),
                            events=all_events,
                        )
                    )

            # Totals
            total_loan_amount = sum(
                sub_loan.loan_amount for sub_loan in financing.sub_loans
            )
            total_interest_paid = sum(p.interest_payment for p in combined)
            first_month_payment = combined[0].payment_amount if combined else 0

            # Weighted average interest rate
            weighted_rate = (
                sum(
                    sub_loan.effective_interest_rate * sub_loan.loan_amount
                    for sub_loan in financing.sub_loans
                    if sub_loan.effective_interest_rate is not None
                )
                / total_loan_amount
                if total_loan_amount > 0
                else 0
            )

            # Weighted average term (in years for display)
            weighted_term = (
                sum(
                    (sub_loan.loan_term_months / 12) * sub_loan.loan_amount
                    for sub_loan in financing.sub_loans
                )
                / total_loan_amount
                if total_loan_amount > 0
                else 0
            )

            schedule = AmortizationSchedule(
                loan_amount=total_loan_amount,
                interest_rate=weighted_rate,
                loan_term_years=int(weighted_term),
                monthly_payment=first_month_payment,
                total_interest_paid=total_interest_paid,
                payments=combined,
                track_schedules=track_schedules,
            )

            return CalculatorResult(
                success=True,
                data=schedule,
                warnings=[
                    "Combined schedule for Israeli mortgage with multiple tracks",
                    f"Includes {len(financing.sub_loans)} tracks",
                ],
            )

        except Exception as e:
            return CalculatorResult(
                success=False,
                errors=[f"Error calculating Israeli mortgage schedule: {str(e)}"],
            )
