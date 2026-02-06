"""Chart components for Streamlit app."""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from ....core.models import Deal
from ....core.calculators import ProFormaCalculator, CashFlowCalculator
from ....core.calculators.proforma import ProForma


def display_equity_buildup_chart(df: pd.DataFrame) -> None:
    """Display equity buildup stacked area chart.
    
    Args:
        df: Pro-forma DataFrame with equity columns
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["equity_from_principal_paydown"],
            name="Principal Paydown",
            stackgroup="one",
            fill="tonexty",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["equity_from_appreciation"],
            name="Appreciation",
            stackgroup="one",
            fill="tonexty",
        )
    )
    fig.update_layout(
        title="Equity Buildup Over Time",
        xaxis_title="Year",
        yaxis_title="Equity ($)",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    st.plotly_chart(fig, use_container_width=True)


def display_income_vs_expenses_chart(df: pd.DataFrame) -> None:
    """Display income vs expenses grouped bar chart.
    
    Args:
        df: Pro-forma DataFrame with income and expense columns
    """
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["effective_gross_income"],
            name="Income",
            marker_color="#10b981",
        )
    )
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["operating_expenses"],
            name="Operating Expenses",
            marker_color="#f59e0b",
        )
    )
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["debt_service"],
            name="Debt Service",
            marker_color="#ef4444",
        )
    )
    fig.update_layout(
        title="Annual Income vs Expenses",
        xaxis_title="Year",
        yaxis_title="Amount ($)",
        barmode="group",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    st.plotly_chart(fig, use_container_width=True)


def display_cash_flow_chart(deal: Deal, years: int = 3) -> None:
    """Display monthly cash flow projection chart.
    
    Args:
        deal: The deal to analyze
        years: Number of years to project
    """
    from ....utils.formatting import format_currency

    calc = CashFlowCalculator(deal)
    result = calc.calculate(years=years)

    if result.success:
        df = result.data.to_dataframe()

        fig = px.line(
            df,
            x=df.index,
            y="pre_tax_cash_flow",
            title=f"Monthly Cash Flow Projection ({years} Years)",
            labels={"pre_tax_cash_flow": "Cash Flow ($)", "index": "Month"},
        )
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        fig.update_traces(line_color="#10b981")
        st.plotly_chart(fig, use_container_width=True)

        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Average Monthly Cash Flow",
                format_currency(result.data.average_monthly_cash_flow),
            )
        with col2:
            st.metric(
                "Year 1 Total",
                format_currency(result.data.total_year1_cash_flow),
            )
        with col3:
            months_positive = result.data.months_to_positive_cash_flow
            st.metric(
                "Months to Positive",
                f"{months_positive} months" if months_positive > 0 else "Immediate",
            )


def display_proforma_chart(deal: Deal, holding_period: int) -> None:
    """Display pro-forma visualization charts.
    
    Args:
        deal: The deal to analyze
        holding_period: Holding period in years
    """
    calc = ProFormaCalculator(deal)
    result = calc.calculate(years=holding_period)

    if not result.success:
        st.error("Unable to generate visualizations")
        return

    df = result.data.to_dataframe()

    # Equity buildup chart
    display_equity_buildup_chart(df)

    # Income vs expenses chart
    display_income_vs_expenses_chart(df)


def display_sensitivity_heatmap(
    x_values: list,
    y_values: list,
    z_values: list,
    x_label: str,
    y_label: str,
    title: str = "Sensitivity Analysis",
) -> None:
    """Display a sensitivity analysis heatmap.
    
    Args:
        x_values: X-axis values (variable 1 percentages)
        y_values: Y-axis values (variable 2 percentages)
        z_values: 2D grid of metric values
        x_label: Label for X-axis
        y_label: Label for Y-axis
        title: Chart title
    """
    fig = go.Figure(
        go.Heatmap(
            x=x_values,
            y=y_values,
            z=z_values,
            colorscale="RdYlGn",
            text=[[f"{val:.1f}%" for val in row] for row in z_values],
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate=f"{x_label}: %{{x}}<br>{y_label}: %{{y}}<br>Value: %{{z:.2f}}<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title=f"{x_label} Change (%)",
        yaxis_title=f"{y_label} Change (%)",
    )

    st.plotly_chart(fig, use_container_width=True)


def display_scenario_comparison_chart(scenario_results: dict) -> None:
    """Display a bar chart comparing metrics across scenarios.
    
    Args:
        scenario_results: Dictionary of scenario name -> metrics dict
    """
    scenarios = list(scenario_results.keys())
    
    # Metrics to compare
    metrics = ["coc_return", "irr", "dscr"]
    metric_labels = ["Cash-on-Cash", "IRR", "DSCR"]

    fig = go.Figure()

    for metric, label in zip(metrics, metric_labels):
        values = []
        for scenario in scenarios:
            val = scenario_results[scenario].get(metric, 0)
            if val is None:
                val = 0
            # Convert to percentage for display
            if metric in ["coc_return", "irr"]:
                val = val * 100
            values.append(val)

        fig.add_trace(
            go.Bar(
                name=label,
                x=scenarios,
                y=values,
                text=[f"{v:.1f}%" if metric in ["coc_return", "irr"] else f"{v:.2f}" for v in values],
                textposition="auto",
            )
        )

    fig.update_layout(
        title="Scenario Comparison",
        xaxis_title="Scenario",
        yaxis_title="Value",
        barmode="group",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    )

    st.plotly_chart(fig, use_container_width=True)


def display_proforma_table(deal: Deal, holding_period: int) -> None:
    """Display pro-forma projections table.
    
    Args:
        deal: The deal to analyze
        holding_period: Holding period in years
    """
    from ....utils.formatting import format_currency

    calc = ProFormaCalculator(deal)
    result = calc.calculate(years=holding_period)

    if result.success:
        df = result.data.to_dataframe()

        # Select key columns for display
        display_cols = [
            "effective_gross_income",
            "operating_expenses",
            "net_operating_income",
            "debt_service",
            "pre_tax_cash_flow",
            "property_value",
            "total_equity",
        ]

        # Format for display
        formatted_df = df[display_cols].copy()
        for col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(lambda x: format_currency(x))

        # Rename columns
        formatted_df.columns = [
            col.replace("_", " ").title() for col in formatted_df.columns
        ]

        # Show specific years
        display_years = [0, 1, 5, 10, holding_period] if holding_period >= 10 else [0, 1, holding_period]
        display_years = [y for y in display_years if y in formatted_df.index]

        st.dataframe(formatted_df.loc[display_years], use_container_width=True)

        # Download full pro-forma
        csv = df.to_csv()
        st.download_button("Download Full Pro-Forma", csv, "proforma.csv", "text/csv")
