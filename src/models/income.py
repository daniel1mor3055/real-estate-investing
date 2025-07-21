"""Income domain model."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class IncomeSource(str, Enum):
    """Types of income sources."""
    
    RENT = "rent"
    PARKING = "parking"
    LAUNDRY = "laundry"
    STORAGE = "storage"
    PET_FEES = "pet_fees"
    UTILITIES = "utilities"
    OTHER = "other"


class IncomeItem(BaseModel):
    """Individual income item."""
    
    source: IncomeSource = Field(..., description="Type of income")
    monthly_amount: float = Field(..., ge=0, description="Monthly income amount")
    description: Optional[str] = Field(None, description="Additional description")
    is_per_unit: bool = Field(False, description="Whether amount is per unit")
    
    def get_total_monthly(self, num_units: int = 1) -> float:
        """Calculate total monthly income."""
        if self.is_per_unit:
            return self.monthly_amount * num_units
        return self.monthly_amount


class Income(BaseModel):
    """Represents all income sources for a property."""
    
    # Primary Income
    monthly_rent_per_unit: float = Field(..., gt=0, description="Monthly rent per unit")
    
    # Vacancy and Credit Loss
    vacancy_rate_percent: float = Field(
        5.0, 
        ge=0, 
        le=50, 
        description="Expected vacancy rate as percentage"
    )
    credit_loss_percent: float = Field(
        1.0, 
        ge=0, 
        le=10, 
        description="Expected credit loss as percentage"
    )
    
    # Additional Income Sources
    other_income: List[IncomeItem] = Field(
        default_factory=list, 
        description="List of other income sources"
    )
    
    # Growth Assumptions
    annual_rent_increase_percent: float = Field(
        3.0, 
        ge=0, 
        le=20, 
        description="Annual rent increase percentage"
    )
    
    @validator("vacancy_rate_percent")
    def validate_vacancy_rate(cls, v):
        """Validate vacancy rate is reasonable."""
        if v > 20:
            # Warning for high vacancy
            import warnings
            warnings.warn(f"High vacancy rate of {v}% - typical rates are 5-10%")
        return v
    
    def calculate_gross_potential_rent(self, num_units: int = 1) -> float:
        """Calculate gross potential rent (100% occupancy)."""
        return self.monthly_rent_per_unit * num_units * 12
    
    def calculate_other_income_annual(self, num_units: int = 1) -> float:
        """Calculate total other income annually."""
        total = 0
        for item in self.other_income:
            total += item.get_total_monthly(num_units) * 12
        return total
    
    def calculate_effective_gross_income(self, num_units: int = 1) -> float:
        """Calculate effective gross income after vacancy and credit loss."""
        gpr = self.calculate_gross_potential_rent(num_units)
        other = self.calculate_other_income_annual(num_units)
        total_potential = gpr + other
        
        # Apply vacancy and credit loss
        vacancy_loss = total_potential * (self.vacancy_rate_percent / 100)
        credit_loss = total_potential * (self.credit_loss_percent / 100)
        
        return total_potential - vacancy_loss - credit_loss
    
    def project_income(self, year: int, num_units: int = 1) -> float:
        """Project income for a specific year with growth."""
        base_income = self.calculate_effective_gross_income(num_units)
        growth_factor = (1 + self.annual_rent_increase_percent / 100) ** (year - 1)
        return base_income * growth_factor
    
    def add_income_source(
        self, 
        source: IncomeSource, 
        monthly_amount: float, 
        description: Optional[str] = None,
        is_per_unit: bool = False
    ) -> None:
        """Add a new income source."""
        item = IncomeItem(
            source=source,
            monthly_amount=monthly_amount,
            description=description,
            is_per_unit=is_per_unit
        )
        self.other_income.append(item)
    
    class Config:
        """Pydantic configuration."""
        
        use_enum_values = True
        validate_assignment = True 