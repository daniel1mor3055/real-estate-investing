"""Streamlit page modules."""

from .detailed_analysis import detailed_analysis_page
from .portfolio import portfolio_comparison_page
from .market_research import market_research_page
from .settings import settings_page

__all__ = [
    "detailed_analysis_page",
    "portfolio_comparison_page",
    "market_research_page",
    "settings_page",
]
