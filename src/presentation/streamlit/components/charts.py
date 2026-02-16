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


def display_operating_metrics_timeseries(deal: Deal, holding_period: int) -> None:
    """Display time series chart for core operating metrics.
    
    Shows annual NOI, Cash Flow, and DSCR over the holding period.
    
    Args:
        deal: The deal to analyze
        holding_period: Holding period in years
    """
    calc = ProFormaCalculator(deal)
    result = calc.calculate(years=holding_period)

    if not result.success:
        st.error("Unable to generate operating metrics chart")
        return

    df = result.data.to_dataframe()
    
    # Exclude year 0 (initial investment year) for operating metrics
    df_operating = df.loc[1:]

    # Create figure with secondary y-axis for DSCR
    fig = go.Figure()

    # NOI line
    fig.add_trace(
        go.Scatter(
            x=df_operating.index,
            y=df_operating["net_operating_income"],
            name="NOI",
            line=dict(color="#10b981", width=2),
            yaxis="y1",
            hovertemplate="Year %{x}<br>NOI: $%{y:,.0f}<extra></extra>",
        )
    )

    # Cash Flow line
    fig.add_trace(
        go.Scatter(
            x=df_operating.index,
            y=df_operating["pre_tax_cash_flow"],
            name="Cash Flow",
            line=dict(color="#3b82f6", width=2),
            yaxis="y1",
            hovertemplate="Year %{x}<br>Cash Flow: $%{y:,.0f}<extra></extra>",
        )
    )

    # DSCR line (on secondary y-axis)
    # Calculate DSCR for each year
    dscr_series = df_operating["net_operating_income"] / df_operating["debt_service"]
    dscr_series = dscr_series.replace([float('inf'), -float('inf')], 999.99)  # Handle division by zero
    
    fig.add_trace(
        go.Scatter(
            x=df_operating.index,
            y=dscr_series,
            name="DSCR",
            line=dict(color="#f59e0b", width=2, dash="dash"),
            yaxis="y2",
            hovertemplate="Year %{x}<br>DSCR: %{y:.2f}x<extra></extra>",
        )
    )

    # Add reference line at DSCR = 1.25 (typical lender requirement)
    fig.add_hline(
        y=1.25,
        line_dash="dot",
        line_color="red",
        annotation_text="Minimum DSCR (1.25x)",
        annotation_position="right",
        yref="y2",
    )

    # Update layout with dual y-axes
    fig.update_layout(
        title="Operating Metrics Over Time",
        xaxis=dict(title="Year", dtick=1),
        yaxis=dict(
            title="Amount ($)",
            side="left",
            showgrid=True,
            tickformat="$,.0f",
        ),
        yaxis2=dict(
            title="DSCR (x)",
            side="right",
            overlaying="y",
            showgrid=False,
            tickformat=".2f",
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)


def display_roe_timeseries(deal: Deal, holding_period: int) -> None:
    """Display time series chart for Return on Equity (ROE).
    
    Shows how ROE evolves over the holding period, providing insights
    into equity efficiency and when to consider refinancing or selling.
    
    Args:
        deal: The deal to analyze
        holding_period: Holding period in years
    """
    calc = ProFormaCalculator(deal)
    result = calc.calculate(years=holding_period)

    if not result.success:
        st.error("Unable to generate ROE chart")
        return

    df = result.data.to_dataframe()
    
    # Exclude year 0 (initial investment year)
    df_roe = df.loc[1:]

    # Create figure
    fig = go.Figure()

    # ROE line
    fig.add_trace(
        go.Scatter(
            x=df_roe.index,
            y=df_roe["roe"] * 100,  # Convert to percentage
            name="ROE",
            line=dict(color="#8b5cf6", width=3),
            fill="tozeroy",
            fillcolor="rgba(139, 92, 246, 0.1)",
            hovertemplate="Year %{x}<br>ROE: %{y:.2f}%<extra></extra>",
        )
    )

    # Add reference lines for target ROE ranges
    fig.add_hline(
        y=8,
        line_dash="dot",
        line_color="orange",
        annotation_text="Minimum Target (8%)",
        annotation_position="right",
    )
    
    fig.add_hline(
        y=12,
        line_dash="dot",
        line_color="green",
        annotation_text="Strong Performance (12%)",
        annotation_position="right",
    )

    # Calculate and display average ROE
    avg_roe = df_roe["roe"].mean() * 100
    
    fig.add_hline(
        y=avg_roe,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Average ROE ({avg_roe:.1f}%)",
        annotation_position="left",
    )

    fig.update_layout(
        title="Return on Equity (ROE) Over Time",
        xaxis=dict(title="Year", dtick=1),
        yaxis=dict(
            title="ROE (%)",
            showgrid=True,
            tickformat=".1f",
            ticksuffix="%",
        ),
        hovermode="x unified",
        height=400,
        annotations=[
            dict(
                text="<i>ROE declining over time may signal opportunities to refinance or sell</i>",
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.15,
                showarrow=False,
                font=dict(size=10, color="gray"),
                xanchor="center",
            )
        ],
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Add interpretation help
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Average ROE",
            f"{avg_roe:.2f}%",
            help="Average Return on Equity across all years"
        )
    
    with col2:
        year_1_roe = df_roe.loc[1, "roe"] * 100
        final_roe = df_roe.iloc[-1]["roe"] * 100
        roe_change = final_roe - year_1_roe
        st.metric(
            f"Year 1 ROE",
            f"{year_1_roe:.2f}%",
            delta=None,
            help="Return on Equity in the first year"
        )
    
    with col3:
        st.metric(
            f"Year {holding_period} ROE",
            f"{final_roe:.2f}%",
            delta=f"{roe_change:+.2f}%",
            help="Return on Equity in the final year vs Year 1"
        )


def display_wealth_metrics_timeseries(deal: Deal, holding_period: int) -> None:
    """Display time series chart for wealth building metrics.
    
    Shows annual Property Value, Total Equity, and Loan Balance.
    
    Args:
        deal: The deal to analyze
        holding_period: Holding period in years
    """
    calc = ProFormaCalculator(deal)
    result = calc.calculate(years=holding_period)

    if not result.success:
        st.error("Unable to generate wealth metrics chart")
        return

    df = result.data.to_dataframe()

    # Create stacked area chart
    fig = go.Figure()

    # Loan Balance (bottom layer)
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["loan_balance"],
            name="Loan Balance",
            fill="tozeroy",
            line=dict(width=0.5, color="#ef4444"),
            fillcolor="rgba(239, 68, 68, 0.3)",
            hovertemplate="Year %{x}<br>Loan Balance: $%{y:,.0f}<extra></extra>",
        )
    )

    # Total Equity (middle layer)
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["total_equity"],
            name="Total Equity",
            fill="tonexty",
            line=dict(width=0.5, color="#10b981"),
            fillcolor="rgba(16, 185, 129, 0.5)",
            hovertemplate="Year %{x}<br>Total Equity: $%{y:,.0f}<extra></extra>",
        )
    )

    # Property Value (top line - not filled)
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["property_value"],
            name="Property Value",
            line=dict(width=3, color="#3b82f6"),
            hovertemplate="Year %{x}<br>Property Value: $%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Wealth Building Metrics Over Time",
        xaxis=dict(title="Year", dtick=1),
        yaxis=dict(
            title="Amount ($)",
            showgrid=True,
            tickformat="$,.0f",
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
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
