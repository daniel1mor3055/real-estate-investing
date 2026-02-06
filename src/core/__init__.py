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
from .strategies import get_investor_strategy, InvestorStrategy

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
    # Strategies
    "get_investor_strategy",
    "InvestorStrategy",
]
