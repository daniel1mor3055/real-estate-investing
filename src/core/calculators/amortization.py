"""Amortization schedule calculator."""

from typing import List
import pandas as pd
import numpy_financial as npf
from pydantic import BaseModel, Field

from .base import Calculator, CalculatorResult


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


class AmortizationSchedule(BaseModel):
    """Complete amortization schedule."""

    loan_amount: float
    interest_rate: float
    loan_term_years: int
    monthly_payment: float
    total_interest_paid: float
    payments: List[AmortizationPayment]

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

        # Check if this is an Israeli mortgage with multiple tracks
        if hasattr(financing, "sub_loans") and financing.sub_loans:
            # Israeli mortgage with multiple tracks
            return self._calculate_israeli_mortgage_schedule(financing)
        else:
            # Simple single loan
            if financing.interest_rate is None:
                return CalculatorResult(
                    success=False,
                    errors=["Interest rate is not set for this financing"],
                )

            schedule = self._calculate_schedule(
                financing.loan_amount,
                financing.interest_rate / 100,
                financing.loan_term_years,
            )

            return CalculatorResult(success=True, data=schedule)

    def _calculate_schedule(
        self, loan_amount: float, annual_rate: float, years: int
    ) -> AmortizationSchedule:
        """Calculate the amortization schedule."""
        monthly_rate = annual_rate / 12
        num_payments = years * 12

        # Calculate monthly payment
        if monthly_rate > 0:
            monthly_payment = float(npf.pmt(monthly_rate, num_payments, -loan_amount))
        else:
            monthly_payment = loan_amount / num_payments

        # Build payment schedule
        payments = []
        balance = loan_amount
        cumulative_principal = 0
        cumulative_interest = 0

        for i in range(1, num_payments + 1):
            # Calculate interest and principal for this payment
            interest = balance * monthly_rate
            principal = monthly_payment - interest

            # Adjust final payment if needed
            if balance < principal:
                principal = balance
                monthly_payment = principal + interest

            balance -= principal
            cumulative_principal += principal
            cumulative_interest += interest

            # Create payment record
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

        # Create schedule
        total_interest = cumulative_interest

        return AmortizationSchedule(
            loan_amount=loan_amount,
            interest_rate=annual_rate * 100,
            loan_term_years=years,
            monthly_payment=monthly_payment,
            total_interest_paid=total_interest,
            payments=payments,
        )

    def _calculate_israeli_mortgage_schedule(self, financing) -> CalculatorResult:
        """Calculate amortization schedule for Israeli mortgage with multiple tracks."""
        try:
            # For Israeli mortgages, we'll create a combined schedule
            # Each sub-loan contributes to the total monthly payment

            all_payments = []
            total_loan_amount = 0
            total_monthly_payment = 0
            total_interest_paid = 0

            # Calculate the longest term to determine schedule length
            max_term_months = max(
                sub_loan.loan_term_years * 12 for sub_loan in financing.sub_loans
            )

            # Initialize balance tracking for each sub-loan
            sub_loan_balances = {
                i: sub_loan.loan_amount 
                for i, sub_loan in enumerate(financing.sub_loans)
            }

            for month in range(1, max_term_months + 1):
                year = (month - 1) // 12 + 1
                month_in_year = ((month - 1) % 12) + 1

                total_payment = 0
                total_principal = 0
                total_interest = 0
                beginning_balance_total = sum(sub_loan_balances.values())

                # Sum payments from all active sub-loans for this month
                for i, sub_loan in enumerate(financing.sub_loans):
                    if month <= sub_loan.loan_term_years * 12 and sub_loan_balances[i] > 0:
                        # This sub-loan is still active
                        sub_payment = sub_loan.monthly_payment
                        current_balance = sub_loan_balances[i]

                        # Calculate interest on current balance
                        effective_rate = sub_loan.effective_interest_rate / 100 / 12
                        interest_portion = current_balance * effective_rate
                        principal_portion = sub_payment - interest_portion

                        # Handle final payment
                        if principal_portion > current_balance:
                            principal_portion = current_balance
                            sub_payment = principal_portion + interest_portion

                        # Update balance
                        sub_loan_balances[i] = max(0, current_balance - principal_portion)

                        total_payment += sub_payment
                        total_principal += principal_portion
                        total_interest += interest_portion

                ending_balance_total = sum(sub_loan_balances.values())

                if total_payment > 0:  # Only add if there's still a payment
                    payment = AmortizationPayment(
                        payment_number=month,
                        year=year,
                        month=month_in_year,
                        beginning_balance=beginning_balance_total,
                        payment_amount=total_payment,
                        principal_payment=total_principal,
                        interest_payment=total_interest,
                        ending_balance=ending_balance_total,
                        cumulative_principal=sum(
                            p.principal_payment for p in all_payments
                        )
                        + total_principal,
                        cumulative_interest=sum(
                            p.interest_payment for p in all_payments
                        )
                        + total_interest,
                    )
                    all_payments.append(payment)

                # Stop if all loans are paid off
                if ending_balance_total <= 0.01:
                    break

            # Calculate totals
            total_loan_amount = sum(
                sub_loan.loan_amount for sub_loan in financing.sub_loans
            )
            total_monthly_payment = sum(
                sub_loan.monthly_payment for sub_loan in financing.sub_loans
            )
            total_interest_paid = sum(p.interest_payment for p in all_payments)

            # Use weighted average interest rate for the schedule
            weighted_rate = (
                sum(
                    sub_loan.effective_interest_rate * sub_loan.loan_amount
                    for sub_loan in financing.sub_loans
                )
                / total_loan_amount
                if total_loan_amount > 0
                else 0
            )

            # Use weighted average term
            weighted_term = (
                sum(
                    sub_loan.loan_term_years * sub_loan.loan_amount
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
                monthly_payment=total_monthly_payment,
                total_interest_paid=total_interest_paid,
                payments=all_payments,
            )

            return CalculatorResult(
                success=True,
                data=schedule,
                warnings=[
                    "This is a combined schedule for Israeli mortgage with multiple tracks",
                    f"Includes {len(financing.sub_loans)} mortgage tracks with different rates and terms",
                ],
            )

        except Exception as e:
            return CalculatorResult(
                success=False,
                errors=[f"Error calculating Israeli mortgage schedule: {str(e)}"],
            )
