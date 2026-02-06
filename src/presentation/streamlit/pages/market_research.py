"""Market research page for Streamlit app."""

import streamlit as st


def market_research_page():
    """Market research page."""
    st.header("Market Research Tools")
    st.info("Access market data and trends")

    st.markdown("### Features coming soon:")
    st.markdown("- Local market rent comparables")
    st.markdown("- Historical appreciation rates")
    st.markdown("- Neighborhood demographics")
    st.markdown("- Economic indicators")

    st.divider()

    # Data sources reference
    st.subheader("Recommended Data Sources")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Free Public Data**")
        st.markdown("""
        - [Zillow Research](https://www.zillow.com/research/) - Home values, rent indices
        - [FRED](https://fred.stlouisfed.org/) - Mortgage rates, CPI, economic data
        - [Census Bureau](https://www.census.gov/) - Demographics, housing stats
        """)

    with col2:
        st.markdown("**Industry Reports**")
        st.markdown("""
        - [NAR Statistics](https://www.nar.realtor/research-and-statistics) - Market trends
        - [CBRE Research](https://www.cbre.com/insights) - Cap rates, market outlook
        - [CoStar](https://www.costar.com/) - Commercial real estate data
        """)

    st.divider()

    # Market assumptions helper
    st.subheader("Default Market Assumptions")
    st.markdown("""
    When analyzing properties, consider using these benchmark ranges:
    
    | Metric | Conservative | Moderate | Aggressive |
    |--------|-------------|----------|------------|
    | Appreciation | 2-3% | 3-4% | 4-6% |
    | Rent Growth | 2-3% | 3-4% | 4-5% |
    | Expense Growth | 3-4% | 2.5-3% | 2-2.5% |
    | Vacancy Rate | 8-10% | 5-7% | 3-5% |
    """)
