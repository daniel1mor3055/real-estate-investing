"""Core domain logic for real estate investment analysis."""

from .models import (
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
from .calculators import (
    Calculator,
    CalculatorResult,
    AmortizationCalculator,
    CashFlowCalculator,
    MetricsCalculator,
    ProFormaCalculator,
)

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
