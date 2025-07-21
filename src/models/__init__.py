"""Domain models for real estate investment analysis."""

from .property import Property, PropertyType
from .financing import Financing, FinancingType
from .expenses import OperatingExpenses, ExpenseCategory
from .income import Income, IncomeSource
from .deal import Deal, DealStatus, MarketAssumptions
from .metrics import MetricResult, MetricType

__all__ = [
    "Property",
    "PropertyType",
    "Financing",
    "FinancingType",
    "OperatingExpenses",
    "ExpenseCategory",
    "Income",
    "IncomeSource",
    "Deal",
    "DealStatus",
    "MarketAssumptions",
    "MetricResult",
    "MetricType",
] 