"""Metric display components for Streamlit app."""

from typing import List, Optional
import streamlit as st

from ....core.calculators.metrics import MetricsBundle
from ....core.models import Deal
from ..styles import RATING_EMOJIS


def display_metric_card(metric) -> None:
    """Display a single metric card with performance-based color coding.
    
    Args:
        metric: MetricResult object to display
    """
    rating_class = metric.performance_rating.lower()
    metric_name = metric.metric_type.replace("_", " ").title()
    emoji = RATING_EMOJIS.get(rating_class, "")

    st.markdown(
        f"""
        <div class='metric-card {rating_class}'>
            <h4>{metric_name}</h4>
            <h2>{metric.formatted_value}</h2>
            <p>{emoji} {metric.performance_rating}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_metrics_overview(deal: Deal, metrics: MetricsBundle) -> None:
    """Display metrics overview with categorized cards.
    
    Args:
        deal: The deal being analyzed
        metrics: Calculated metrics bundle
    """
    st.subheader("Investment Summary")

    # Deal score prominently displayed
    if metrics.deal_score:
        score = metrics.deal_score.value
        color = "green" if score >= 70 else "orange" if score >= 50 else "red"
        st.markdown(
            f"<h1 style='text-align: center; color: {color};'>Deal Score: {score:.0f}/100</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='text-align: center;'>Based on {metrics.deal_score.metadata['investor_profile']} investor profile</p>",
            unsafe_allow_html=True,
        )

    st.subheader("Key Performance Indicators")

    # Define performance rating order for sorting (best to worst)
    rating_order = {"excellent": 0, "good": 1, "fair": 2, "poor": 3, "unknown": 4}

    # Organize metrics by category and sort by performance
    profitability_metrics = sorted(
        [metrics.noi_year1, metrics.cap_rate, metrics.cash_flow_year1],
        key=lambda m: rating_order.get(m.performance_rating.lower(), 4),
    )

    return_metrics = sorted(
        [m for m in [metrics.coc_return, metrics.irr, metrics.equity_multiple] if m],
        key=lambda m: rating_order.get(m.performance_rating.lower(), 4),
    )

    risk_metrics = sorted(
        [m for m in [metrics.dscr, metrics.break_even_ratio] if m],
        key=lambda m: rating_order.get(m.performance_rating.lower(), 4),
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Profitability Metrics**")
        for metric in profitability_metrics:
            display_metric_card(metric)

    with col2:
        st.markdown("**Return Metrics**")
        for metric in return_metrics:
            display_metric_card(metric)

    with col3:
        st.markdown("**Risk Metrics**")
        for metric in risk_metrics:
            display_metric_card(metric)


def display_deal_summary(deal: Deal) -> None:
    """Display a summary of the deal details.
    
    Args:
        deal: The deal to summarize
    """
    from ....utils.formatting import format_currency, format_percentage

    st.subheader("Deal Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Purchase Price", format_currency(deal.property.purchase_price))
        st.metric("Total Cash Needed", format_currency(deal.get_total_cash_needed()))

    with col2:
        if not deal.financing.is_cash_purchase:
            st.metric("Loan Amount", format_currency(deal.financing.loan_amount or 0))
            st.metric("Interest Rate", format_percentage(deal.financing.interest_rate / 100 if deal.financing.interest_rate else 0))
        else:
            st.metric("Financing", "All Cash")
            st.metric("Loan Amount", "$0")

    with col3:
        st.metric("Monthly Rent", format_currency(deal.income.monthly_rent_per_unit * deal.property.num_units))
        st.metric("Year 1 NOI", format_currency(deal.get_year_1_noi()))


def display_metrics_comparison(
    metrics_list: List[MetricsBundle],
    labels: List[str],
) -> None:
    """Display a comparison table of metrics across multiple scenarios or deals.
    
    Args:
        metrics_list: List of MetricsBundle objects to compare
        labels: Labels for each set of metrics
    """
    import pandas as pd

    data = []
    for label, metrics in zip(labels, metrics_list):
        row = {
            "Scenario": label,
            "Cap Rate": metrics.cap_rate.formatted_value,
            "Cash-on-Cash": metrics.coc_return.formatted_value,
            "DSCR": metrics.dscr.formatted_value,
        }
        if metrics.irr:
            row["IRR"] = metrics.irr.formatted_value
        if metrics.equity_multiple:
            row["Equity Multiple"] = metrics.equity_multiple.formatted_value
        if metrics.deal_score:
            row["Deal Score"] = f"{metrics.deal_score.value:.0f}"
        data.append(row)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
