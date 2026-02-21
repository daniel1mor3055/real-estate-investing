"""Domain models for real estate investment analysis."""

from .property import Property, PropertyType
from .financing import (
    Financing,
    FinancingType,
    SubLoan,
    IsraeliMortgageTrack,
    RepaymentMethod,
    GraceType,
    GracePeriod,
    PrepaymentOption,
    RateChange,
    Prepayment,
)
from .expenses import OperatingExpenses, ExpenseCategory
from .income import Income, IncomeSource
from .deal import Deal, DealStatus, MarketAssumptions
from .metrics import MetricResult, MetricType

__all__ = [
    "Property",
    "PropertyType",
    "Financing",
    "FinancingType",
    "SubLoan",
    "IsraeliMortgageTrack",
    "RepaymentMethod",
    "GraceType",
    "GracePeriod",
    "PrepaymentOption",
    "RateChange",
    "Prepayment",
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
