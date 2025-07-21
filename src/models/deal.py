"""Deal domain model - the main aggregate root."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, validator

from .property import Property
from .financing import Financing
from .income import Income
from .expenses import OperatingExpenses


class DealStatus(str, Enum):
    """Status of a real estate deal."""
    
    ANALYZING = "analyzing"
    UNDER_CONTRACT = "under_contract"
    DUE_DILIGENCE = "due_diligence"
    CLOSED = "closed"
    PASSED = "passed"
    WITHDRAWN = "withdrawn"


class MarketAssumptions(BaseModel):
    """Market assumptions for projections."""
    
    annual_appreciation_percent: float = Field(
        3.5, 
        ge=-10, 
        le=20, 
        description="Annual property appreciation rate"
    )
    sales_expense_percent: float = Field(
        7.0, 
        ge=0, 
        le=15, 
        description="Sales expenses as percentage of sale price"
    )
    inflation_rate_percent: float = Field(
        2.5, 
        ge=0, 
        le=10, 
        description="General inflation rate"
    )


class Deal(BaseModel):
    """Represents a complete real estate investment deal."""
    
    # Deal Identification
    deal_id: str = Field(..., description="Unique deal identifier")
    deal_name: str = Field(..., description="Descriptive name for the deal")
    status: DealStatus = Field(
        DealStatus.ANALYZING, 
        description="Current status of the deal"
    )
    created_date: datetime = Field(
        default_factory=datetime.now, 
        description="Date deal was created"
    )
    
    # Core Components
    property: Property = Field(..., description="Property details")
    financing: Financing = Field(..., description="Financing structure")
    income: Income = Field(..., description="Income projections")
    expenses: OperatingExpenses = Field(..., description="Operating expenses")
    
    # Market Assumptions
    market_assumptions: MarketAssumptions = Field(
        default_factory=MarketAssumptions,
        description="Market assumptions for projections"
    )
    
    # Analysis Parameters
    holding_period_years: int = Field(
        10, 
        ge=1, 
        le=30, 
        description="Expected holding period in years"
    )
    
    # Notes and Documentation
    notes: Optional[str] = Field(None, description="Additional notes about the deal")
    
    @validator("financing")
    def validate_financing_matches_property(cls, v, values):
        """Ensure financing is calculated based on property price."""
        if "property" in values:
            property = values["property"]
            v.calculate_loan_details(property.purchase_price)
        return v
    
    def get_total_cash_needed(self) -> float:
        """Calculate total cash needed to close the deal."""
        if self.financing.is_cash_purchase:
            return self.property.total_acquisition_cost
        else:
            return (
                self.financing.down_payment_amount +
                self.property.closing_costs +
                self.property.rehab_budget +
                (self.financing.loan_amount * self.financing.loan_points / 100)
            )
    
    def get_year_1_noi(self) -> float:
        """Calculate Year 1 Net Operating Income."""
        egi = self.income.calculate_effective_gross_income(self.property.num_units)
        opex = self.expenses.calculate_total_operating_expenses(egi, self.property.num_units)
        return egi - opex
    
    def get_year_1_cash_flow(self) -> float:
        """Calculate Year 1 pre-tax cash flow."""
        return self.get_year_1_noi() - self.financing.annual_debt_service
    
    def get_cap_rate(self) -> float:
        """Calculate capitalization rate."""
        if self.property.purchase_price > 0:
            return self.get_year_1_noi() / self.property.purchase_price
        return 0
    
    def get_cash_on_cash_return(self) -> float:
        """Calculate cash-on-cash return."""
        total_cash = self.get_total_cash_needed()
        if total_cash > 0:
            return self.get_year_1_cash_flow() / total_cash
        return 0
    
    def get_debt_service_coverage_ratio(self) -> float:
        """Calculate DSCR."""
        if self.financing.annual_debt_service > 0:
            return self.get_year_1_noi() / self.financing.annual_debt_service
        return float('inf')  # No debt = infinite coverage
    
    def get_gross_rent_multiplier(self) -> float:
        """Calculate GRM."""
        annual_rent = self.income.monthly_rent_per_unit * self.property.num_units * 12
        if annual_rent > 0:
            return self.property.purchase_price / annual_rent
        return 0
    
    def to_dict(self) -> dict:
        """Convert deal to dictionary for serialization."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: dict) -> "Deal":
        """Create deal from dictionary."""
        return cls(**data)
    
    class Config:
        """Pydantic configuration."""
        
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        } 