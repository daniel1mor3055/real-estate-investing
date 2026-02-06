"""Investment strategies for different investor profiles."""

from .investor import (
    InvestorStrategy,
    CashFlowInvestor,
    BalancedInvestor,
    AppreciationInvestor,
    get_investor_strategy
)

__all__ = [
    "InvestorStrategy",
    "CashFlowInvestor",
    "BalancedInvestor", 
    "AppreciationInvestor",
    "get_investor_strategy",
] 