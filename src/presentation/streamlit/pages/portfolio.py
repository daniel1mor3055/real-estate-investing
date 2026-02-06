"""Portfolio comparison page for Streamlit app."""

import streamlit as st


def portfolio_comparison_page():
    """Portfolio comparison page."""
    st.header("Portfolio Comparison")
    st.info("Compare multiple properties side-by-side")

    st.markdown("### Features coming soon:")
    st.markdown("- Load multiple property analyses")
    st.markdown("- Side-by-side metric comparison")
    st.markdown("- Portfolio optimization suggestions")
    st.markdown("- Risk/return scatter plots")

    # Placeholder for future implementation
    st.divider()
    
    st.subheader("Quick Start")
    st.markdown("""
    1. Run analyses on individual properties in the Detailed Analysis page
    2. Save each analysis to your portfolio
    3. Return here to compare and optimize your investment strategy
    """)

    # Show session state deals if any
    if "saved_deals" in st.session_state and st.session_state["saved_deals"]:
        st.subheader("Saved Deals")
        for deal_name in st.session_state["saved_deals"]:
            st.write(f"- {deal_name}")
    else:
        st.info("No deals saved yet. Analyze a property first.")
