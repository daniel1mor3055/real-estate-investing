"""Streamlit GUI for Real Estate Investment Analysis."""

import streamlit as st

from .styles import apply_custom_styles
from .pages import (
    detailed_analysis_page,
    portfolio_comparison_page,
    market_research_page,
    settings_page,
)


def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Real Estate Investment Analyzer",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def main():
    """Main application entry point."""
    configure_page()
    apply_custom_styles()

    st.title("🏠 Real Estate Investment Analyzer")
    st.markdown("### Professional-grade analysis for rental property investments")

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        [
            "Detailed Analysis",
            "Portfolio Comparison",
            "Market Research",
            "Settings",
        ],
    )

    # Route to selected page
    if page == "Detailed Analysis":
        detailed_analysis_page()
    elif page == "Portfolio Comparison":
        portfolio_comparison_page()
    elif page == "Market Research":
        market_research_page()
    elif page == "Settings":
        settings_page()


if __name__ == "__main__":
    main()
