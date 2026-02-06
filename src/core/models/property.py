"""Property domain model."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, validator


class PropertyType(str, Enum):
    """Types of real estate properties."""
    
    SINGLE_FAMILY = "single_family"
    MULTI_FAMILY = "multi_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"


class Property(BaseModel):
    """Represents a real estate property."""
    
    # Basic Information
    address: str = Field(..., description="Property address")
    property_type: PropertyType = Field(..., description="Type of property")
    
    # Physical Characteristics
    square_footage: Optional[int] = Field(None, gt=0, description="Total square footage")
    num_units: int = Field(1, ge=1, description="Number of rental units")
    bedrooms: int = Field(..., ge=0, description="Total number of bedrooms")
    bathrooms: float = Field(..., ge=0, description="Total number of bathrooms")
    year_built: Optional[int] = Field(None, gt=1800, le=2100, description="Year property was built")
    
    # Purchase Details
    purchase_price: float = Field(..., gt=0, description="Purchase price in dollars")
    closing_costs: float = Field(0, ge=0, description="Closing costs in dollars")
    rehab_budget: float = Field(0, ge=0, description="Initial renovation budget in dollars")
    
    # Market Analysis
    after_repair_value: Optional[float] = Field(None, gt=0, description="Estimated value after repairs")
    market_rent_per_unit: Optional[float] = Field(None, gt=0, description="Market rent per unit")
    
    @validator("purchase_price")
    def validate_purchase_price(cls, v):
        """Ensure purchase price is reasonable."""
        if v < 10000:
            raise ValueError("Purchase price seems too low. Please verify.")
        if v > 100000000:
            raise ValueError("Purchase price seems too high. Please verify.")
        return v
    
    @validator("closing_costs")
    def validate_closing_costs(cls, v, values):
        """Ensure closing costs are reasonable relative to purchase price."""
        if "purchase_price" in values:
            purchase_price = values["purchase_price"]
            if v > purchase_price * 0.1:  # More than 10% seems high
                raise ValueError("Closing costs seem high relative to purchase price")
        return v
    
    @property
    def total_acquisition_cost(self) -> float:
        """Calculate total cost to acquire and prepare the property."""
        return self.purchase_price + self.closing_costs + self.rehab_budget
    
    @property
    def cost_per_unit(self) -> float:
        """Calculate cost per rental unit."""
        return self.total_acquisition_cost / self.num_units
    
    @property
    def cost_per_sqft(self) -> Optional[float]:
        """Calculate cost per square foot."""
        if self.square_footage:
            return self.total_acquisition_cost / self.square_footage
        return None
    
    class Config:
        """Pydantic configuration."""
        
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            PropertyType: lambda v: v.value,
        } 