"""Financing domain model."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, validator
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


class Financing(BaseModel):
    """Represents financing structure for a property."""
    
    # Financing Type
    financing_type: FinancingType = Field(..., description="Type of financing")
    is_cash_purchase: bool = Field(False, description="Whether this is an all-cash purchase")
    
    # Loan Terms
    down_payment_percent: float = Field(
        20.0, 
        ge=0, 
        le=100, 
        description="Down payment as percentage of purchase price"
    )
    interest_rate: float = Field(
        7.0, 
        ge=0, 
        le=30, 
        description="Annual interest rate as percentage"
    )
    loan_term_years: int = Field(30, ge=1, le=40, description="Loan term in years")
    loan_points: float = Field(0, ge=0, le=5, description="Loan points as percentage")
    
    # Calculated Fields (set after property price is known)
    loan_amount: Optional[float] = Field(None, ge=0, description="Total loan amount")
    down_payment_amount: Optional[float] = Field(None, ge=0, description="Down payment in dollars")
    monthly_payment: Optional[float] = Field(None, description="Monthly P&I payment")
    
    @validator("is_cash_purchase")
    def validate_cash_purchase(cls, v, values):
        """Ensure cash purchase has 100% down payment."""
        if v and "down_payment_percent" in values:
            if values["down_payment_percent"] != 100:
                raise ValueError("Cash purchase must have 100% down payment")
        return v
    
    @validator("down_payment_percent")
    def validate_down_payment_by_type(cls, v, values):
        """Validate down payment based on financing type."""
        if "financing_type" in values:
            financing_type = values["financing_type"]
            
            if financing_type == FinancingType.FHA and v < 3.5:
                raise ValueError("FHA loans require minimum 3.5% down payment")
            elif financing_type == FinancingType.VA and v < 0:
                raise ValueError("VA loans allow 0% down payment")
            elif financing_type == FinancingType.CONVENTIONAL and v < 5:
                raise ValueError("Conventional loans typically require minimum 5% down payment")
        
        return v
    
    def calculate_loan_details(self, purchase_price: float) -> None:
        """Calculate loan amount and payment details based on purchase price."""
        if self.is_cash_purchase:
            self.loan_amount = 0
            self.down_payment_amount = purchase_price
            self.monthly_payment = 0
        else:
            self.down_payment_amount = purchase_price * (self.down_payment_percent / 100)
            self.loan_amount = purchase_price - self.down_payment_amount
            
            if self.loan_amount > 0 and self.interest_rate > 0:
                monthly_rate = self.interest_rate / 100 / 12
                num_payments = self.loan_term_years * 12
                self.monthly_payment = float(
                    npf.pmt(monthly_rate, num_payments, -self.loan_amount)
                )
            else:
                self.monthly_payment = 0
    
    @property
    def total_interest_paid(self) -> float:
        """Calculate total interest over the life of the loan."""
        if self.monthly_payment and self.loan_amount:
            total_paid = self.monthly_payment * self.loan_term_years * 12
            return total_paid - self.loan_amount
        return 0
    
    @property
    def annual_debt_service(self) -> float:
        """Calculate annual debt service (P&I)."""
        return (self.monthly_payment or 0) * 12
    
    @property
    def loan_to_value_ratio(self) -> float:
        """Calculate LTV ratio."""
        if self.is_cash_purchase:
            return 0
        return 100 - self.down_payment_percent
    
    class Config:
        """Pydantic configuration."""
        
        use_enum_values = True
        validate_assignment = True 