"""Financing domain model with Israeli mortgage tracks (מסלולים)."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator, model_validator
import numpy_financial as npf


class FinancingType(str, Enum):
    """Types of financing options."""

    CASH = "cash"
    CONVENTIONAL = "conventional"
    FHA = "fha"
    VA = "va"
    HARD_MONEY = "hard_money"
    PRIVATE_MONEY = "private_money"
    SELLER_FINANCING = "seller_financing"


class IsraeliMortgageTrack(str, Enum):
    """Israeli mortgage tracks (מסלולים) as per Bank of Israel regulations."""

    FIXED_UNLINKED = "fixed_unlinked"  # ריבית קבועה לא צמודה - קל"צ
    PRIME_RATE = "prime_rate"  # מסלול פריים (backward compat)
    FIXED_RATE_LINKED = "fixed_rate_linked"  # ריבית קבועה צמודה
    VARIABLE_LINKED_5Y = "variable_linked_5y"  # משתנה צמודה כל 5 שנים
    VARIABLE_UNLINKED_5Y = "variable_unlinked_5y"  # משתנה לא צמודה כל 5 שנים
    VARIABLE_LINKED_1Y = "variable_linked_1y"  # משתנה צמודה כל שנה
    VARIABLE_LINKED_2Y = "variable_linked_2y"  # משתנה צמודה כל שנתיים
    VARIABLE_LINKED_10Y = "variable_linked_10y"  # משתנה צמודה כל 10 שנים

    @property
    def hebrew_name(self) -> str:
        """Get Hebrew name for the track."""
        names = {
            "fixed_unlinked": 'ריבית קבועה לא צמודה (קל"צ)',
            "prime_rate": "מסלול פריים",
            "fixed_rate_linked": "ריבית קבועה צמודה",
            "variable_linked_5y": "משתנה צמודה כל 5 שנים",
            "variable_unlinked_5y": "משתנה לא צמודה כל 5 שנים",
            "variable_linked_1y": "משתנה צמודה כל שנה",
            "variable_linked_2y": "משתנה צמודה כל שנתיים",
            "variable_linked_10y": "משתנה צמודה כל 10 שנים",
        }
        return names.get(self.value, self.value)

    @property
    def is_fixed_rate(self) -> bool:
        """Check if this track has a fixed interest rate."""
        return self in [
            IsraeliMortgageTrack.FIXED_UNLINKED,
            IsraeliMortgageTrack.FIXED_RATE_LINKED,
        ]

    @property
    def is_cpi_linked(self) -> bool:
        """Check if this track has CPI-linked principal."""
        return self in [
            IsraeliMortgageTrack.FIXED_RATE_LINKED,
            IsraeliMortgageTrack.VARIABLE_LINKED_5Y,
            IsraeliMortgageTrack.VARIABLE_LINKED_1Y,
            IsraeliMortgageTrack.VARIABLE_LINKED_2Y,
            IsraeliMortgageTrack.VARIABLE_LINKED_10Y,
        ]

    @property
    def is_prime_based(self) -> bool:
        """Check if this track is based on Bank of Israel prime rate."""
        return self == IsraeliMortgageTrack.PRIME_RATE

    @property
    def is_variable_rate(self) -> bool:
        """Check if this is a variable-rate track (including Prime)."""
        return not self.is_fixed_rate

    @property
    def reset_period_months(self) -> Optional[int]:
        """Rate reset period in months. None for fixed/prime tracks."""
        periods = {
            "variable_linked_5y": 60,
            "variable_unlinked_5y": 60,
            "variable_linked_1y": 12,
            "variable_linked_2y": 24,
            "variable_linked_10y": 120,
        }
        return periods.get(self.value)


class RepaymentMethod(str, Enum):
    """Repayment methods for Israeli mortgage tracks."""

    SPITZER = "spitzer"  # שפיצר — constant annuity payment
    EQUAL_PRINCIPAL = "equal_principal"  # קרן שווה — declining payment
    BULLET = "bullet"  # בלון — interest-only, principal repaid at maturity


class GraceType(str, Enum):
    """Types of grace period."""

    INTEREST_ONLY = "interest_only"  # Pay interest, no principal reduction
    FULL_DEFERRAL = "full_deferral"  # No payments, interest capitalizes


class GracePeriod(BaseModel):
    """Grace period configuration for a mortgage track."""

    duration_months: int = Field(
        ..., ge=1, le=120, description="Grace period length in months"
    )
    grace_type: GraceType = Field(..., description="Type of grace period")


class PrepaymentOption(str, Enum):
    """How a prepayment affects the remaining loan."""

    REDUCE_TERM = "reduce_term"  # Keep payment amount, shorten loan duration
    REDUCE_PAYMENT = "reduce_payment"  # Keep term, lower monthly payment


class RateChange(BaseModel):
    """Scheduled interest rate change event."""

    month: int = Field(
        ..., ge=1, description="Month when the new rate takes effect"
    )
    delta: float = Field(
        ...,
        description="Change in percentage points (e.g., 1.5 means the rate increases by 1.5%)",
    )


class Prepayment(BaseModel):
    """Scheduled prepayment event."""

    month: int = Field(..., ge=1, description="Month when prepayment occurs")
    amount: float = Field(..., gt=0, description="Prepayment amount in currency")
    option: PrepaymentOption = Field(
        default=PrepaymentOption.REDUCE_PAYMENT,
        description="How prepayment affects the loan",
    )


class SubLoan(BaseModel):
    """Represents a single sub-loan track of an Israeli mortgage."""

    # Loan identification
    name: str = Field(..., description="Name/identifier for this sub-loan track")

    # Israeli mortgage track type
    track_type: IsraeliMortgageTrack = Field(
        ..., description="Israeli mortgage track type"
    )

    # Financial terms
    loan_amount: float = Field(
        ..., ge=0, description="Principal amount for this sub-loan track"
    )
    base_interest_rate: float = Field(
        ..., ge=0, le=30, description="Base annual interest rate as percentage"
    )
    loan_term_months: int = Field(
        ..., ge=1, le=360, description="Loan term in months (1-360)"
    )

    # Israeli-specific parameters
    bank_of_israel_rate: Optional[float] = Field(
        None,
        ge=0,
        le=20,
        description="Bank of Israel official rate for prime calculations",
    )
    expected_cpi: Optional[float] = Field(
        None, ge=-5, le=20, description="Expected annual CPI for linked tracks"
    )

    # Repayment configuration
    repayment_method: RepaymentMethod = Field(
        default=RepaymentMethod.SPITZER,
        description="Repayment method for this track",
    )
    grace_period: Optional[GracePeriod] = Field(
        None, description="Optional grace period at the start of the loan"
    )
    rate_changes: List[RateChange] = Field(
        default_factory=list,
        description="Scheduled interest rate changes over the life of the loan",
    )
    prepayments: List[Prepayment] = Field(
        default_factory=list,
        description="Scheduled prepayments",
    )

    # Calculated fields
    effective_interest_rate: Optional[float] = Field(
        None, description="Calculated effective rate"
    )
    monthly_payment: Optional[float] = Field(
        None, description="Monthly P&I payment for this sub-loan"
    )
    cpi_adjusted_principal: Optional[float] = Field(
        None, description="CPI-adjusted principal amount"
    )

    @model_validator(mode="after")
    def validate_subloan_parameters(self):
        """Validate track-specific parameters and event boundaries."""
        # Prime rate track must have Bank of Israel rate
        if (
            self.track_type == IsraeliMortgageTrack.PRIME_RATE
            and self.bank_of_israel_rate is None
        ):
            raise ValueError(
                "Prime rate track must specify bank_of_israel_rate parameter"
            )

        # CPI-linked tracks must have expected CPI
        if self.track_type.is_cpi_linked and self.expected_cpi is None:
            raise ValueError("CPI-linked tracks must specify expected_cpi parameter")

        # Non-prime tracks shouldn't have BoI rate
        if not self.track_type.is_prime_based and self.bank_of_israel_rate is not None:
            raise ValueError("Non-prime tracks should not specify bank_of_israel_rate")

        # Non-CPI-linked tracks shouldn't have CPI
        if not self.track_type.is_cpi_linked and self.expected_cpi is not None:
            raise ValueError("Non-CPI-linked tracks should not specify expected_cpi")

        # Validate events are within loan term
        term_months = self.loan_term_months

        for rc in self.rate_changes:
            if rc.month > term_months:
                raise ValueError(
                    f"Rate change at month {rc.month} exceeds loan term ({term_months} months)"
                )

        for pp in self.prepayments:
            if pp.month > term_months:
                raise ValueError(
                    f"Prepayment at month {pp.month} exceeds loan term ({term_months} months)"
                )

        if self.grace_period and self.grace_period.duration_months >= term_months:
            raise ValueError("Grace period must be shorter than loan term")

        return self

    def calculate_effective_rate(self) -> float:
        """Calculate the effective interest rate for this Israeli mortgage track."""
        if self.track_type == IsraeliMortgageTrack.PRIME_RATE:
            if self.bank_of_israel_rate is not None:
                effective_rate = self.bank_of_israel_rate + 1.5
            else:
                effective_rate = self.base_interest_rate
        else:
            effective_rate = self.base_interest_rate

        self.effective_interest_rate = effective_rate
        return effective_rate

    def calculate_cpi_adjusted_principal(self, years_elapsed: float = 0) -> float:
        """Calculate CPI-adjusted principal for linked tracks."""
        if not self.track_type.is_cpi_linked or self.expected_cpi is None:
            self.cpi_adjusted_principal = self.loan_amount
            return self.loan_amount

        cpi_factor = (1 + self.expected_cpi / 100) ** years_elapsed
        adjusted_principal = self.loan_amount * cpi_factor
        self.cpi_adjusted_principal = adjusted_principal
        return adjusted_principal

    def calculate_payment(self, years_elapsed: float = 0) -> float:
        """Calculate the initial monthly payment for this track.

        For Spitzer: constant annuity payment.
        For Equal Principal: first month's payment (highest).
        For Bullet: interest-only payment.
        """
        if self.loan_amount <= 0:
            self.monthly_payment = 0
            return 0

        effective_rate = self.calculate_effective_rate()
        principal_amount = self.calculate_cpi_adjusted_principal(years_elapsed)
        num_payments = self.loan_term_months

        if effective_rate <= 0:
            if self.repayment_method == RepaymentMethod.BULLET:
                self.monthly_payment = 0
            else:
                self.monthly_payment = principal_amount / num_payments
        else:
            monthly_rate = effective_rate / 100 / 12

            if self.repayment_method == RepaymentMethod.SPITZER:
                self.monthly_payment = float(
                    npf.pmt(monthly_rate, num_payments, -principal_amount)
                )
            elif self.repayment_method == RepaymentMethod.EQUAL_PRINCIPAL:
                principal_per_month = principal_amount / num_payments
                first_interest = principal_amount * monthly_rate
                self.monthly_payment = principal_per_month + first_interest
            elif self.repayment_method == RepaymentMethod.BULLET:
                self.monthly_payment = principal_amount * monthly_rate

        return self.monthly_payment

    @property
    def loan_term_years(self) -> float:
        """Loan term converted to years (for display/compatibility)."""
        return self.loan_term_months / 12

    @property
    def total_interest_paid(self) -> float:
        """Calculate total interest over the life of this sub-loan."""
        if self.monthly_payment and self.loan_amount:
            total_paid = self.monthly_payment * self.loan_term_months
            principal_base = self.cpi_adjusted_principal or self.loan_amount
            return total_paid - principal_base
        return 0

    @property
    def track_description(self) -> str:
        """Get a description of this mortgage track."""
        descriptions = {
            IsraeliMortgageTrack.FIXED_UNLINKED: "Fixed rate, not linked to index. Most predictable payments.",
            IsraeliMortgageTrack.PRIME_RATE: "Variable rate based on Bank of Israel prime (BoI rate + 1.5%).",
            IsraeliMortgageTrack.FIXED_RATE_LINKED: "Fixed rate, principal linked to CPI index.",
            IsraeliMortgageTrack.VARIABLE_LINKED_5Y: "Rate resets every 5 years, principal linked to CPI.",
            IsraeliMortgageTrack.VARIABLE_UNLINKED_5Y: "Rate resets every 5 years, not linked to index.",
            IsraeliMortgageTrack.VARIABLE_LINKED_1Y: "Rate resets yearly, principal linked to CPI.",
            IsraeliMortgageTrack.VARIABLE_LINKED_2Y: "Rate resets every 2 years, principal linked to CPI.",
            IsraeliMortgageTrack.VARIABLE_LINKED_10Y: "Rate resets every 10 years, principal linked to CPI.",
        }
        return descriptions.get(self.track_type, "Unknown track type")


class Financing(BaseModel):
    """Represents Israeli mortgage financing structure with regulatory compliance."""

    # Financing Type (for compatibility)
    financing_type: FinancingType = Field(..., description="Primary type of financing")
    is_cash_purchase: bool = Field(
        False, description="Whether this is an all-cash purchase"
    )

    # Israeli mortgage tracks (up to 3)
    sub_loans: List[SubLoan] = Field(
        default_factory=list, description="List of mortgage tracks (max 3)"
    )

    # Legacy fields for backward compatibility
    down_payment_percent: float = Field(
        20.0, ge=0, le=100, description="Down payment as percentage of purchase price"
    )
    interest_rate: Optional[float] = Field(
        None, ge=0, le=30, description="Legacy: Annual interest rate as percentage"
    )
    loan_term_years: Optional[int] = Field(
        None, ge=1, le=40, description="Legacy: Loan term in years"
    )
    loan_points: float = Field(0, ge=0, le=5, description="Loan points as percentage")

    # Calculated Fields
    loan_amount: Optional[float] = Field(
        None, ge=0, description="Total loan amount across all tracks"
    )
    down_payment_amount: Optional[float] = Field(
        None, ge=0, description="Down payment in dollars"
    )
    monthly_payment: Optional[float] = Field(
        None, description="Total monthly P&I payment"
    )

    @validator("sub_loans")
    def validate_sub_loans_count(cls, v):
        """Ensure maximum of 3 sub-loans."""
        if len(v) > 3:
            raise ValueError("Maximum of 3 mortgage tracks allowed per mortgage")
        return v

    @model_validator(mode="after")
    def validate_israeli_mortgage_regulations(self):
        """Validate Israeli Bank regulations for mortgage composition."""
        if len(self.sub_loans) == 0:
            return self

        total_amount = sum(sub_loan.loan_amount for sub_loan in self.sub_loans)
        if total_amount == 0:
            return self

        fixed_rate_amount = sum(
            sub_loan.loan_amount
            for sub_loan in self.sub_loans
            if sub_loan.track_type.is_fixed_rate
        )
        variable_rate_amount = sum(
            sub_loan.loan_amount
            for sub_loan in self.sub_loans
            if sub_loan.track_type.is_variable_rate
        )

        # Bank of Israel: at least 1/3 must be fixed-rate
        fixed_rate_ratio = fixed_rate_amount / total_amount
        if fixed_rate_ratio < (1 / 3 - 0.001):
            raise ValueError(
                f"Israeli regulation requires at least 1/3 of mortgage to be fixed-rate tracks. Current: {fixed_rate_ratio:.1%}"
            )

        # Bank of Israel: variable rate limited to max 2/3
        variable_rate_ratio = variable_rate_amount / total_amount
        if variable_rate_ratio > (2 / 3 + 0.001):
            raise ValueError(
                f"Israeli regulation limits variable rate tracks to maximum 2/3 of mortgage. Current: {variable_rate_ratio:.1%}"
            )

        return self

    @validator("is_cash_purchase")
    def validate_cash_purchase(cls, v, values):
        """Ensure cash purchase has 100% down payment and no sub-loans."""
        if v:
            if (
                "down_payment_percent" in values
                and values["down_payment_percent"] != 100
            ):
                raise ValueError("Cash purchase must have 100% down payment")
            if "sub_loans" in values and len(values["sub_loans"]) > 0:
                raise ValueError("Cash purchase cannot have mortgage tracks")
        return v

    @classmethod
    def create_simple_loan(
        cls,
        financing_type: FinancingType,
        down_payment_percent: float,
        interest_rate: float,
        loan_term_years: int,
        loan_points: float = 0,
        is_cash_purchase: bool = False,
    ) -> "Financing":
        """Factory method to create a simple single-loan financing (backward compatibility)."""
        return cls(
            financing_type=financing_type,
            is_cash_purchase=is_cash_purchase,
            down_payment_percent=down_payment_percent,
            interest_rate=interest_rate,
            loan_term_years=loan_term_years,
            loan_points=loan_points,
            sub_loans=[],
        )

    @classmethod
    def create_israeli_mortgage(
        cls,
        financing_type: FinancingType,
        down_payment_percent: float,
        mortgage_tracks: List[SubLoan],
        loan_points: float = 0,
    ) -> "Financing":
        """Factory method to create Israeli mortgage with regulatory compliance."""
        return cls(
            financing_type=financing_type,
            is_cash_purchase=False,
            down_payment_percent=down_payment_percent,
            sub_loans=mortgage_tracks,
            loan_points=loan_points,
        )

    def calculate_loan_details(
        self, purchase_price: float, years_elapsed: float = 0
    ) -> None:
        """Calculate loan amount and payment details based on purchase price."""
        if self.is_cash_purchase:
            self.loan_amount = 0
            self.down_payment_amount = purchase_price
            self.monthly_payment = 0
            return

        self.down_payment_amount = purchase_price * (self.down_payment_percent / 100)
        total_loan_amount = purchase_price - self.down_payment_amount

        if len(self.sub_loans) == 0:
            # Legacy single loan mode
            self.loan_amount = total_loan_amount
            if self.loan_amount > 0 and self.interest_rate and self.interest_rate > 0:
                monthly_rate = self.interest_rate / 100 / 12
                num_payments = (self.loan_term_years or 30) * 12
                self.monthly_payment = float(
                    npf.pmt(monthly_rate, num_payments, -self.loan_amount)
                )
            else:
                self.monthly_payment = 0
        else:
            total_track_amount = sum(track.loan_amount for track in self.sub_loans)

            if total_track_amount > total_loan_amount + 0.01:
                raise ValueError(
                    f"Total track amount ({total_track_amount:,.0f}) exceeds available loan amount ({total_loan_amount:,.0f})"
                )

            self.loan_amount = total_track_amount

            total_monthly_payment = 0
            for track in self.sub_loans:
                payment = track.calculate_payment(years_elapsed)
                total_monthly_payment += payment

            self.monthly_payment = total_monthly_payment

    @property
    def total_interest_paid(self) -> float:
        """Calculate total interest over the life of all tracks."""
        if len(self.sub_loans) == 0:
            if self.monthly_payment and self.loan_amount:
                total_paid = self.monthly_payment * (self.loan_term_years or 30) * 12
                return total_paid - self.loan_amount
            return 0
        else:
            return sum(track.total_interest_paid for track in self.sub_loans)

    @property
    def annual_debt_service(self) -> float:
        """Calculate annual debt service (monthly payment * 12)."""
        return (self.monthly_payment or 0) * 12

    def get_israeli_mortgage_summary(self) -> dict:
        """Get a summary of Israeli mortgage tracks with regulatory compliance info."""
        if self.is_cash_purchase:
            return {
                "type": "cash",
                "total_amount": 0,
                "monthly_payment": 0,
                "tracks": [],
                "regulatory_compliance": {"status": "N/A - Cash Purchase"},
            }

        if len(self.sub_loans) == 0:
            return {
                "type": "single_loan",
                "total_amount": self.loan_amount,
                "monthly_payment": self.monthly_payment,
                "interest_rate": self.interest_rate,
                "term_years": self.loan_term_years,
                "tracks": [],
                "regulatory_compliance": {"status": "N/A - Legacy Mode"},
            }

        total_amount = sum(track.loan_amount for track in self.sub_loans)
        fixed_rate_amount = sum(
            track.loan_amount
            for track in self.sub_loans
            if track.track_type.is_fixed_rate
        )
        variable_rate_amount = sum(
            track.loan_amount
            for track in self.sub_loans
            if track.track_type.is_variable_rate
        )

        fixed_rate_ratio = fixed_rate_amount / total_amount if total_amount > 0 else 0
        variable_rate_ratio = variable_rate_amount / total_amount if total_amount > 0 else 0

        return {
            "type": "israeli_mortgage",
            "total_amount": self.loan_amount,
            "monthly_payment": self.monthly_payment,
            "tracks": [
                {
                    "name": track.name,
                    "track_type": track.track_type.value,
                    "hebrew_name": track.track_type.hebrew_name,
                    "amount": track.loan_amount,
                    "percentage": (
                        (track.loan_amount / total_amount * 100)
                        if total_amount > 0
                        else 0
                    ),
                    "base_rate": track.base_interest_rate,
                    "effective_rate": track.effective_interest_rate,
                    "monthly_payment": track.monthly_payment,
                    "term_months": track.loan_term_months,
                    "repayment_method": track.repayment_method.value,
                    "is_cpi_linked": track.track_type.is_cpi_linked,
                    "has_grace_period": track.grace_period is not None,
                    "grace_months": (
                        track.grace_period.duration_months
                        if track.grace_period
                        else 0
                    ),
                    "rate_changes_count": len(track.rate_changes),
                    "prepayments_count": len(track.prepayments),
                    "description": track.track_description,
                }
                for track in self.sub_loans
            ],
            "regulatory_compliance": {
                "status": "Compliant",
                "fixed_rate_ratio": fixed_rate_ratio,
                "variable_rate_ratio": variable_rate_ratio,
                "fixed_rate_requirement": f"{fixed_rate_ratio:.1%} (Required: ≥33.3%)",
                "variable_rate_limit": f"{variable_rate_ratio:.1%} (Limit: ≤66.7%)",
            },
        }
