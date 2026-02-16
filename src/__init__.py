"""Real Estate Investment Analysis Package.

This package provides tools for analyzing real estate investment deals,
including financial calculations and pro-forma projections.

Structure:
- core: Domain models and calculators
- services: Business logic coordination
- analysis: Advanced sensitivity and scenario analysis
- adapters: External interfaces and persistence
- presentation: CLI and Streamlit UI
- utils: Shared utilities
"""

# Re-export commonly used items from core for convenience
from .core.models import (
    Property,
    PropertyType,
    Financing,
    FinancingType,
    SubLoan,
    IsraeliMortgageTrack,
    OperatingExpenses,
    ExpenseCategory,
    Income,
    IncomeSource,
    Deal,
    DealStatus,
    MarketAssumptions,
    MetricResult,
    MetricType,
)

from .core.calculators import (
    Calculator,
    CalculatorResult,
    AmortizationCalculator,
    CashFlowCalculator,
    MetricsCalculator,
    ProFormaCalculator,
)

# Version
__version__ = "2.0.0"

__all__ = [
    # Models
    "Property",
    "PropertyType",
    "Financing",
    "FinancingType",
    "SubLoan",
    "IsraeliMortgageTrack",
    "OperatingExpenses",
    "ExpenseCategory",
    "Income",
    "IncomeSource",
    "Deal",
    "DealStatus",
    "MarketAssumptions",
    "MetricResult",
    "MetricType",
    # Calculators
    "Calculator",
    "CalculatorResult",
    "AmortizationCalculator",
    "CashFlowCalculator",
    "MetricsCalculator",
    "ProFormaCalculator",
]
