"""Operating expenses domain model."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class ExpenseCategory(str, Enum):
    """Categories of operating expenses."""
    
    # Fixed Expenses
    PROPERTY_TAX = "property_tax"
    INSURANCE = "insurance"
    HOA = "hoa"
    
    # Variable Expenses
    UTILITIES = "utilities"
    MAINTENANCE = "maintenance"
    REPAIRS = "repairs"
    LANDSCAPING = "landscaping"
    SNOW_REMOVAL = "snow_removal"
    PEST_CONTROL = "pest_control"
    GARBAGE = "garbage"
    
    # Management
    PROPERTY_MANAGEMENT = "property_management"
    LEASING_FEES = "leasing_fees"
    ADVERTISING = "advertising"
    LEGAL = "legal"
    ACCOUNTING = "accounting"
    
    # Reserves
    CAPEX_RESERVE = "capex_reserve"
    VACANCY_RESERVE = "vacancy_reserve"
    
    OTHER = "other"


class ExpenseItem(BaseModel):
    """Individual expense item."""
    
    category: ExpenseCategory = Field(..., description="Expense category")
    annual_amount: float = Field(None, ge=0, description="Annual expense amount")
    monthly_amount: float = Field(None, ge=0, description="Monthly expense amount")
    percentage_of_income: float = Field(None, ge=0, le=100, description="Percentage of EGI")
    description: Optional[str] = Field(None, description="Additional description")
    is_per_unit: bool = Field(False, description="Whether amount is per unit")
    
    @validator("annual_amount", "monthly_amount", "percentage_of_income")
    def validate_expense_specification(cls, v, values):
        """Ensure at least one expense specification is provided."""
        if all(
            val is None 
            for key, val in values.items() 
            if key in ["annual_amount", "monthly_amount", "percentage_of_income"]
        ):
            if v is None:
                raise ValueError(
                    "Must specify either annual_amount, monthly_amount, or percentage_of_income"
                )
        return v
    
    def calculate_annual_expense(self, egi: float = 0, num_units: int = 1) -> float:
        """Calculate annual expense amount."""
        if self.annual_amount is not None:
            base = self.annual_amount
        elif self.monthly_amount is not None:
            base = self.monthly_amount * 12
        elif self.percentage_of_income is not None and egi > 0:
            return egi * (self.percentage_of_income / 100)
        else:
            return 0
        
        if self.is_per_unit:
            return base * num_units
        return base


class OperatingExpenses(BaseModel):
    """Represents all operating expenses for a property."""
    
    # Fixed Expenses
    property_tax_annual: float = Field(..., ge=0, description="Annual property tax")
    insurance_annual: float = Field(..., ge=0, description="Annual property insurance")
    hoa_monthly: float = Field(0, ge=0, description="Monthly HOA fees")
    
    # Variable Expenses (as percentage of EGI)
    maintenance_percent: float = Field(
        5.0, 
        ge=0, 
        le=30, 
        description="Maintenance as percentage of EGI"
    )
    property_management_percent: float = Field(
        8.0, 
        ge=0, 
        le=15, 
        description="Property management as percentage of EGI"
    )
    
    # Reserves (as percentage of EGI)
    capex_reserve_percent: float = Field(
        5.0, 
        ge=0, 
        le=20, 
        description="CapEx reserve as percentage of EGI"
    )
    
    # Utilities (if landlord paid)
    landlord_paid_utilities_monthly: float = Field(
        0, 
        ge=0, 
        description="Monthly utilities paid by landlord"
    )
    
    # Additional Expenses
    other_expenses: List[ExpenseItem] = Field(
        default_factory=list, 
        description="List of other expense items"
    )
    
    # Growth Assumptions
    annual_expense_growth_percent: float = Field(
        3.0, 
        ge=0, 
        le=20, 
        description="Annual expense growth percentage"
    )
    
    @validator("property_tax_annual")
    def validate_property_tax(cls, v):
        """Validate property tax is reasonable."""
        if v > 50000:
            import warnings
            warnings.warn(f"High property tax of ${v:,.0f} - please verify")
        return v
    
    def calculate_fixed_expenses(self) -> float:
        """Calculate total fixed expenses annually."""
        return (
            self.property_tax_annual + 
            self.insurance_annual + 
            (self.hoa_monthly * 12) +
            (self.landlord_paid_utilities_monthly * 12)
        )
    
    def calculate_variable_expenses(self, egi: float) -> float:
        """Calculate variable expenses based on EGI."""
        maintenance = egi * (self.maintenance_percent / 100)
        management = egi * (self.property_management_percent / 100)
        capex = egi * (self.capex_reserve_percent / 100)
        
        return maintenance + management + capex
    
    def calculate_other_expenses(self, egi: float, num_units: int = 1) -> float:
        """Calculate total other expenses."""
        total = 0
        for expense in self.other_expenses:
            total += expense.calculate_annual_expense(egi, num_units)
        return total
    
    def calculate_total_operating_expenses(self, egi: float, num_units: int = 1) -> float:
        """Calculate total operating expenses."""
        fixed = self.calculate_fixed_expenses()
        variable = self.calculate_variable_expenses(egi)
        other = self.calculate_other_expenses(egi, num_units)
        
        return fixed + variable + other
    
    def project_expenses(self, year: int, egi: float, num_units: int = 1) -> float:
        """
        Project expenses for a specific year with growth.
        
        Note: Only fixed expenses grow with expense_growth_factor.
        Variable expenses (% of EGI) automatically grow as EGI grows.
        """
        growth_factor = (1 + self.annual_expense_growth_percent / 100) ** (year - 1)
        
        # Fixed expenses grow with expense inflation
        fixed = self.calculate_fixed_expenses() * growth_factor
        
        # Variable expenses (% of EGI) don't need additional growth factor
        # They already grow because they're calculated from the grown EGI
        variable = self.calculate_variable_expenses(egi)
        
        # Other expenses - need to determine if they're fixed or variable
        other = self.calculate_other_expenses(egi, num_units)
        
        return fixed + variable + other
    
    def get_expense_breakdown(self, egi: float, num_units: int = 1, year: int = 1) -> Dict[str, float]:
        """
        Get detailed breakdown of all expenses.
        
        Args:
            egi: Effective Gross Income for the year
            num_units: Number of units
            year: Year number (for applying growth to fixed expenses)
        """
        growth_factor = (1 + self.annual_expense_growth_percent / 100) ** (year - 1)
        
        breakdown = {
            # Fixed expenses with growth
            "property_tax": self.property_tax_annual * growth_factor,
            "insurance": self.insurance_annual * growth_factor,
            "hoa": self.hoa_monthly * 12 * growth_factor,
            "utilities": self.landlord_paid_utilities_monthly * 12 * growth_factor,
            # Variable expenses (% of EGI) - no additional growth factor needed
            "maintenance": egi * (self.maintenance_percent / 100),
            "property_management": egi * (self.property_management_percent / 100),
            "capex_reserve": egi * (self.capex_reserve_percent / 100),
        }
        
        # Add other expenses
        for expense in self.other_expenses:
            key = f"{expense.category.value}_{expense.description or 'misc'}"
            breakdown[key] = expense.calculate_annual_expense(egi, num_units)
        
        return breakdown
    
    def add_expense(
        self,
        category: ExpenseCategory,
        annual_amount: Optional[float] = None,
        monthly_amount: Optional[float] = None,
        percentage_of_income: Optional[float] = None,
        description: Optional[str] = None,
        is_per_unit: bool = False
    ) -> None:
        """Add a new expense item."""
        item = ExpenseItem(
            category=category,
            annual_amount=annual_amount,
            monthly_amount=monthly_amount,
            percentage_of_income=percentage_of_income,
            description=description,
            is_per_unit=is_per_unit
        )
        self.other_expenses.append(item)
    
    class Config:
        """Pydantic configuration."""
        
        use_enum_values = True
        validate_assignment = True 