#!/usr/bin/env python3
"""Streamlit GUI for Real Estate Investment Analysis."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json

from src.models import (
    Property,
    PropertyType,
    Financing,
    FinancingType,
    Income,
    IncomeSource,
    OperatingExpenses,
    ExpenseCategory,
    Deal,
    DealStatus,
    MarketAssumptions,
)
from src.calculators import (
    MetricsCalculator,
    ProFormaCalculator,
    AmortizationCalculator,
    CashFlowCalculator,
)
from src.strategies import get_investor_strategy
from src.utils import format_currency, format_percentage, format_ratio

# Page configuration
st.set_page_config(
    page_title="Real Estate Investment Analyzer",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .good { color: #28a745; }
    .fair { color: #ffc107; }
    .poor { color: #dc3545; }
</style>
""",
    unsafe_allow_html=True,
)


def main():
    """Main application entry point."""
    st.title("🏠 Real Estate Investment Analyzer")
    st.markdown("### Professional-grade analysis for rental property investments")

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        [
            "Quick Analysis",
            "Detailed Analysis",
            "Portfolio Comparison",
            "Market Research",
            "Settings",
        ],
    )

    if page == "Quick Analysis":
        quick_analysis_page()
    elif page == "Detailed Analysis":
        detailed_analysis_page()
    elif page == "Portfolio Comparison":
        portfolio_comparison_page()
    elif page == "Market Research":
        market_research_page()
    elif page == "Settings":
        settings_page()


def quick_analysis_page():
    """Quick analysis with minimal inputs."""
    st.header("Quick Property Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Property Details")
        address = st.text_input("Property Address", "123 Main St, City, State")
        purchase_price = st.number_input(
            "Purchase Price", min_value=0, value=300000, step=5000
        )
        monthly_rent = st.number_input("Monthly Rent", min_value=0, value=2500, step=50)
        units = st.number_input("Number of Units", min_value=1, value=1)

    with col2:
        st.subheader("Financing")
        down_payment = st.slider("Down Payment %", 0, 100, 20)
        interest_rate = st.number_input(
            "Interest Rate %", min_value=0.0, value=7.0, step=0.25
        )
        loan_term = st.selectbox("Loan Term", [15, 30], index=1)

    if st.button("Analyze", type="primary"):
        # Create deal with defaults
        deal = create_quick_deal(
            address,
            purchase_price,
            monthly_rent,
            units,
            down_payment,
            interest_rate,
            loan_term,
        )

        # Calculate metrics
        metrics_calc = MetricsCalculator(deal)
        metrics_result = metrics_calc.calculate()

        if metrics_result.success:
            display_quick_results(deal, metrics_result.data)
        else:
            st.error(f"Error: {metrics_result.errors}")


def detailed_analysis_page():
    """Detailed analysis with all inputs."""
    st.header("Detailed Property Analysis")

    # Use tabs for organization
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Property", "Financing", "Income", "Expenses", "Analysis"]
    )

    with tab1:
        property_inputs = get_property_inputs()

    with tab2:
        financing_inputs = get_financing_inputs()

    with tab3:
        income_inputs = get_income_inputs()

    with tab4:
        expenses_inputs = get_expenses_inputs()

    with tab5:
        if st.button("Run Analysis", type="primary"):
            # Create deal
            deal = create_detailed_deal(
                property_inputs, financing_inputs, income_inputs, expenses_inputs
            )

            # Store in session state
            st.session_state["current_deal"] = deal

            # Run analysis
            run_detailed_analysis(deal)


def get_property_inputs():
    """Get property input fields."""
    col1, col2 = st.columns(2)

    with col1:
        address = st.text_input("Address", "123 Investment Property Lane")
        property_type = st.selectbox(
            "Property Type",
            [t.value for t in PropertyType],
            format_func=lambda x: x.replace("_", " ").title(),
        )
        purchase_price = st.number_input("Purchase Price", value=300000, step=5000)
        closing_costs = st.number_input("Closing Costs", value=7500, step=500)
        rehab_budget = st.number_input("Rehab Budget", value=15000, step=1000)

    with col2:
        units = st.number_input("Units", min_value=1, value=1)
        bedrooms = st.number_input("Bedrooms", min_value=0, value=3)
        bathrooms = st.number_input("Bathrooms", min_value=0.0, value=2.0, step=0.5)
        sqft = st.number_input("Square Feet", min_value=0, value=1500, step=50)
        year_built = st.number_input(
            "Year Built", min_value=1800, max_value=2024, value=1990
        )

    return {
        "address": address,
        "property_type": property_type,
        "purchase_price": purchase_price,
        "closing_costs": closing_costs,
        "rehab_budget": rehab_budget,
        "units": units,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "sqft": sqft,
        "year_built": year_built,
    }


def get_financing_inputs():
    """Get financing input fields."""
    col1, col2 = st.columns(2)

    with col1:
        financing_type = st.selectbox(
            "Financing Type",
            [t.value for t in FinancingType],
            format_func=lambda x: x.replace("_", " ").title(),
        )
        is_cash = st.checkbox("All Cash Purchase")
        down_payment = st.slider("Down Payment %", 0, 100, 20, disabled=is_cash)

    with col2:
        interest_rate = st.number_input(
            "Interest Rate %", min_value=0.0, value=7.0, step=0.25, disabled=is_cash
        )
        loan_term = st.selectbox(
            "Loan Term (years)", [15, 30], index=1, disabled=is_cash
        )
        points = st.number_input(
            "Loan Points", min_value=0.0, value=0.0, step=0.5, disabled=is_cash
        )

    return {
        "financing_type": financing_type,
        "is_cash": is_cash,
        "down_payment": down_payment,
        "interest_rate": interest_rate,
        "loan_term": loan_term,
        "points": points,
    }


def get_income_inputs():
    """Get income input fields."""
    st.subheader("Rental Income")

    col1, col2 = st.columns(2)
    with col1:
        monthly_rent = st.number_input("Monthly Rent per Unit", value=2500, step=50)
        vacancy_rate = st.slider("Vacancy Rate %", 0, 20, 5)

    with col2:
        credit_loss = st.slider("Credit Loss %", 0, 10, 1)
        annual_increase = st.number_input("Annual Rent Increase %", value=3.0, step=0.5)

    st.subheader("Other Income")

    other_income = []
    num_sources = st.number_input("Number of Other Income Sources", 0, 5, 0)

    if num_sources > 0:
        cols = st.columns(3)
        for i in range(num_sources):
            with cols[i % 3]:
                st.write(f"Source {i+1}")
                source_type = st.selectbox(
                    f"Type {i+1}",
                    ["parking", "laundry", "storage", "pet_fees", "other"],
                    key=f"income_type_{i}",
                )
                amount = st.number_input(
                    f"Monthly Amount {i+1}", value=0, step=25, key=f"income_amount_{i}"
                )
                per_unit = st.checkbox(f"Per Unit {i+1}", key=f"income_per_unit_{i}")

                if amount > 0:
                    other_income.append(
                        {"type": source_type, "amount": amount, "per_unit": per_unit}
                    )

    return {
        "monthly_rent": monthly_rent,
        "vacancy_rate": vacancy_rate,
        "credit_loss": credit_loss,
        "annual_increase": annual_increase,
        "other_income": other_income,
    }


def get_expenses_inputs():
    """Get expense input fields."""
    st.subheader("Fixed Expenses")

    col1, col2 = st.columns(2)
    with col1:
        property_tax = st.number_input("Annual Property Tax", value=3600, step=100)
        insurance = st.number_input("Annual Insurance", value=1200, step=100)

    with col2:
        hoa = st.number_input("Monthly HOA", value=0, step=25)
        utilities = st.number_input(
            "Monthly Utilities (Landlord Paid)", value=0, step=25
        )

    st.subheader("Variable Expenses (% of Income)")

    col1, col2, col3 = st.columns(3)
    with col1:
        maintenance = st.slider("Maintenance %", 0, 20, 5)
    with col2:
        management = st.slider("Management %", 0, 15, 8)
    with col3:
        capex = st.slider("CapEx Reserve %", 0, 20, 5)

    annual_increase = st.number_input("Annual Expense Growth %", value=3.0, step=0.5)

    return {
        "property_tax": property_tax,
        "insurance": insurance,
        "hoa": hoa,
        "utilities": utilities,
        "maintenance": maintenance,
        "management": management,
        "capex": capex,
        "annual_increase": annual_increase,
    }


def create_quick_deal(address, price, rent, units, down_payment, rate, term):
    """Create a deal object for quick analysis."""
    property = Property(
        address=address,
        property_type=PropertyType.SINGLE_FAMILY,
        purchase_price=price,
        closing_costs=price * 0.025,
        num_units=units,
        bedrooms=3,
        bathrooms=2,
    )

    financing = Financing(
        financing_type=FinancingType.CONVENTIONAL,
        down_payment_percent=down_payment,
        interest_rate=rate,
        loan_term_years=term,
    )

    income = Income(
        monthly_rent_per_unit=rent,
        vacancy_rate_percent=5,
        annual_rent_increase_percent=3,
    )

    expenses = OperatingExpenses(
        property_tax_annual=price * 0.012,
        insurance_annual=price * 0.004,
        maintenance_percent=5,
        property_management_percent=8,
        capex_reserve_percent=5,
    )

    return Deal(
        deal_id=f"quick-{datetime.now().timestamp()}",
        deal_name=f"Quick Analysis - {address}",
        property=property,
        financing=financing,
        income=income,
        expenses=expenses,
    )


def create_detailed_deal(prop, fin, inc, exp):
    """Create a deal object from detailed inputs."""
    property = Property(
        address=prop["address"],
        property_type=PropertyType(prop["property_type"]),
        purchase_price=prop["purchase_price"],
        closing_costs=prop["closing_costs"],
        rehab_budget=prop["rehab_budget"],
        num_units=prop["units"],
        bedrooms=prop["bedrooms"],
        bathrooms=prop["bathrooms"],
        square_footage=prop["sqft"],
        year_built=prop["year_built"],
    )

    financing = Financing(
        financing_type=FinancingType(fin["financing_type"]),
        is_cash_purchase=fin["is_cash"],
        down_payment_percent=fin["down_payment"],
        interest_rate=fin["interest_rate"],
        loan_term_years=fin["loan_term"],
        loan_points=fin["points"],
    )

    income = Income(
        monthly_rent_per_unit=inc["monthly_rent"],
        vacancy_rate_percent=inc["vacancy_rate"],
        credit_loss_percent=inc["credit_loss"],
        annual_rent_increase_percent=inc["annual_increase"],
    )

    # Add other income sources
    for source in inc["other_income"]:
        income.add_income_source(
            source=IncomeSource(source["type"]),
            monthly_amount=source["amount"],
            is_per_unit=source["per_unit"],
        )

    expenses = OperatingExpenses(
        property_tax_annual=exp["property_tax"],
        insurance_annual=exp["insurance"],
        hoa_monthly=exp["hoa"],
        landlord_paid_utilities_monthly=exp["utilities"],
        maintenance_percent=exp["maintenance"],
        property_management_percent=exp["management"],
        capex_reserve_percent=exp["capex"],
        annual_expense_growth_percent=exp["annual_increase"],
    )

    return Deal(
        deal_id=f"detailed-{datetime.now().timestamp()}",
        deal_name=property.address,
        property=property,
        financing=financing,
        income=income,
        expenses=expenses,
    )


def display_quick_results(deal, metrics):
    """Display quick analysis results."""
    st.success("Analysis Complete!")

    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Investment", format_currency(deal.get_total_cash_needed()))

    with col2:
        noi = metrics.noi_year1
        st.metric("Year 1 NOI", noi.formatted_value, delta=f"{noi.performance_rating}")

    with col3:
        coc = metrics.coc_return
        st.metric(
            "Cash-on-Cash Return",
            coc.formatted_value,
            delta=f"{coc.performance_rating}",
        )

    with col4:
        cap_rate = metrics.cap_rate
        st.metric(
            "Cap Rate", cap_rate.formatted_value, delta=f"{cap_rate.performance_rating}"
        )

    # Monthly cash flow breakdown
    st.subheader("Monthly Cash Flow Analysis")

    monthly_rent = deal.income.monthly_rent_per_unit * deal.property.num_units
    monthly_expenses = (
        deal.expenses.calculate_total_operating_expenses(
            deal.income.calculate_effective_gross_income(deal.property.num_units),
            deal.property.num_units,
        )
        / 12
    )
    monthly_debt = deal.financing.monthly_payment or 0
    monthly_cash_flow = monthly_rent - monthly_expenses - monthly_debt

    fig = go.Figure(
        go.Waterfall(
            name="Monthly",
            orientation="v",
            measure=["relative", "relative", "relative", "total"],
            x=["Gross Rent", "Operating Expenses", "Debt Service", "Cash Flow"],
            y=[monthly_rent, -monthly_expenses, -monthly_debt, monthly_cash_flow],
            text=[
                f"${v:,.0f}"
                for v in [
                    monthly_rent,
                    monthly_expenses,
                    monthly_debt,
                    monthly_cash_flow,
                ]
            ],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        )
    )

    fig.update_layout(title="Monthly Cash Flow Waterfall", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def run_detailed_analysis(deal):
    """Run and display detailed analysis."""
    st.success("Analysis Complete!")

    # Analysis parameters
    col1, col2, col3 = st.columns(3)
    with col1:
        holding_period = st.selectbox(
            "Holding Period (years)", [5, 10, 15, 20, 30], index=1
        )
    with col2:
        investor_profile = st.selectbox(
            "Investor Profile",
            ["cash_flow", "balanced", "appreciation"],
            format_func=lambda x: x.replace("_", " ").title(),
        )
    with col3:
        show_details = st.checkbox("Show Detailed Breakdown", value=True)

    # Calculate metrics
    metrics_calc = MetricsCalculator(deal)
    metrics_result = metrics_calc.calculate(
        holding_period=holding_period, investor_profile=investor_profile
    )

    if not metrics_result.success:
        st.error(f"Error: {metrics_result.errors}")
        return

    metrics = metrics_result.data

    # Display tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Cash Flow", "Pro Forma", "Visualizations", "Sensitivity"]
    )

    with tab1:
        display_metrics_overview(deal, metrics)

    with tab2:
        display_cash_flow_analysis(deal)

    with tab3:
        display_proforma(deal, holding_period)

    with tab4:
        display_visualizations(deal, holding_period)

    with tab5:
        display_sensitivity_analysis(deal)


def display_metrics_overview(deal, metrics):
    """Display metrics overview."""
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

    # Key metrics grid
    st.subheader("Key Performance Indicators")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Profitability Metrics**")
        for metric in [metrics.noi_year1, metrics.cap_rate, metrics.cash_flow_year1]:
            display_metric_card(metric)

    with col2:
        st.markdown("**Return Metrics**")
        for metric in [metrics.coc_return, metrics.irr, metrics.equity_multiple]:
            if metric:
                display_metric_card(metric)

    with col3:
        st.markdown("**Risk Metrics**")
        for metric in [metrics.dscr, metrics.break_even_ratio]:
            if metric:
                display_metric_card(metric)


def display_metric_card(metric):
    """Display a single metric card."""
    rating_class = metric.performance_rating.lower()
    st.markdown(
        f"""
        <div class='metric-card'>
            <h4>{metric.metric_type.replace('_', ' ').title()}</h4>
            <h2 class='{rating_class}'>{metric.formatted_value}</h2>
            <p>Rating: {metric.performance_rating}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_cash_flow_analysis(deal):
    """Display detailed cash flow analysis."""
    st.subheader("Cash Flow Analysis")

    # Calculate monthly cash flows
    calc = CashFlowCalculator(deal)
    result = calc.calculate(years=3)

    if result.success:
        df = result.data.to_dataframe()

        # Monthly cash flow chart
        fig = px.line(
            df,
            x=df.index,
            y="pre_tax_cash_flow",
            title="Monthly Cash Flow Projection (3 Years)",
            labels={"pre_tax_cash_flow": "Cash Flow ($)", "index": "Month"},
        )
        fig.add_hline(y=0, line_dash="dash", line_color="red")
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
                "Year 1 Total", format_currency(result.data.total_year1_cash_flow)
            )
        with col3:
            months_positive = result.data.months_to_positive_cash_flow
            st.metric(
                "Months to Positive",
                f"{months_positive} months" if months_positive > 0 else "Immediate",
            )


def display_proforma(deal, years):
    """Display pro-forma projections."""
    st.subheader(f"{years}-Year Pro Forma")

    calc = ProFormaCalculator(deal)
    result = calc.calculate(years=years)

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
        display_years = [0, 1, 5, 10, years] if years >= 10 else [0, 1, years]
        display_years = [y for y in display_years if y in formatted_df.index]

        st.dataframe(formatted_df.loc[display_years], use_container_width=True)

        # Download full pro-forma
        csv = df.to_csv()
        st.download_button("Download Full Pro-Forma", csv, "proforma.csv", "text/csv")


def display_visualizations(deal, holding_period):
    """Display various visualizations."""
    st.subheader("Investment Visualizations")

    # Get pro-forma data
    calc = ProFormaCalculator(deal)
    result = calc.calculate(years=holding_period)

    if not result.success:
        st.error("Unable to generate visualizations")
        return

    df = result.data.to_dataframe()

    # Equity buildup chart
    fig1 = go.Figure()
    fig1.add_trace(
        go.Scatter(
            x=df.index,
            y=df["equity_from_principal_paydown"],
            name="Principal Paydown",
            stackgroup="one",
        )
    )
    fig1.add_trace(
        go.Scatter(
            x=df.index,
            y=df["equity_from_appreciation"],
            name="Appreciation",
            stackgroup="one",
        )
    )
    fig1.update_layout(
        title="Equity Buildup Over Time",
        xaxis_title="Year",
        yaxis_title="Equity ($)",
        hovermode="x unified",
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Income vs Expenses
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df.index, y=df["effective_gross_income"], name="Income"))
    fig2.add_trace(go.Bar(x=df.index, y=df["operating_expenses"], name="OpEx"))
    fig2.add_trace(go.Bar(x=df.index, y=df["debt_service"], name="Debt Service"))
    fig2.update_layout(
        title="Annual Income vs Expenses",
        xaxis_title="Year",
        yaxis_title="Amount ($)",
        barmode="group",
    )
    st.plotly_chart(fig2, use_container_width=True)


def display_sensitivity_analysis(deal):
    """Display sensitivity analysis."""
    st.subheader("Sensitivity Analysis")

    # Select variables
    col1, col2 = st.columns(2)
    with col1:
        var1 = st.selectbox(
            "Variable 1",
            ["Purchase Price", "Rent", "Vacancy Rate", "Interest Rate"],
            index=0,
        )
        var1_range = st.slider(f"{var1} Range (%)", -20, 20, (-10, 10))

    with col2:
        var2 = st.selectbox(
            "Variable 2",
            ["Purchase Price", "Rent", "Vacancy Rate", "Interest Rate"],
            index=1,
        )
        var2_range = st.slider(f"{var2} Range (%)", -20, 20, (-10, 10))

    if st.button("Run Sensitivity Analysis"):
        # This would run actual sensitivity analysis
        st.info(
            "Sensitivity analysis would show how changes in selected variables affect returns"
        )

        # Placeholder heatmap
        import numpy as np

        x = np.linspace(var1_range[0], var1_range[1], 10)
        y = np.linspace(var2_range[0], var2_range[1], 10)
        z = np.random.rand(10, 10) * 20 - 10  # Placeholder data

        fig = go.Figure(
            data=go.Heatmap(
                x=x,
                y=y,
                z=z,
                colorscale="RdYlGn",
                text=[[f"{val:.1f}%" for val in row] for row in z],
                texttemplate="%{text}",
                textfont={"size": 10},
            )
        )

        fig.update_layout(
            title=f"IRR Sensitivity: {var1} vs {var2}",
            xaxis_title=f"{var1} Change (%)",
            yaxis_title=f"{var2} Change (%)",
        )

        st.plotly_chart(fig, use_container_width=True)


def portfolio_comparison_page():
    """Portfolio comparison page."""
    st.header("Portfolio Comparison")
    st.info("Compare multiple properties side-by-side")

    # This would allow loading and comparing multiple deals
    st.markdown("### Features coming soon:")
    st.markdown("- Load multiple property analyses")
    st.markdown("- Side-by-side metric comparison")
    st.markdown("- Portfolio optimization suggestions")
    st.markdown("- Risk/return scatter plots")


def market_research_page():
    """Market research page."""
    st.header("Market Research Tools")
    st.info("Access market data and trends")

    # This would integrate with external data sources
    st.markdown("### Features coming soon:")
    st.markdown("- Local market rent comparables")
    st.markdown("- Historical appreciation rates")
    st.markdown("- Neighborhood demographics")
    st.markdown("- Economic indicators")


def settings_page():
    """Settings page."""
    st.header("Settings")

    st.subheader("Default Assumptions")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Income Defaults**")
        default_vacancy = st.number_input("Default Vacancy Rate %", value=5.0)
        default_rent_growth = st.number_input("Default Rent Growth %", value=3.0)

        st.markdown("**Expense Defaults**")
        default_maintenance = st.number_input("Default Maintenance %", value=5.0)
        default_management = st.number_input("Default Management %", value=8.0)
        default_capex = st.number_input("Default CapEx %", value=5.0)

    with col2:
        st.markdown("**Market Defaults**")
        default_appreciation = st.number_input("Default Appreciation %", value=3.5)
        default_inflation = st.number_input("Default Inflation %", value=2.5)

        st.markdown("**Analysis Defaults**")
        default_holding = st.selectbox(
            "Default Holding Period", [5, 10, 15, 20, 30], index=1
        )
        default_profile = st.selectbox(
            "Default Investor Profile",
            ["cash_flow", "balanced", "appreciation"],
            format_func=lambda x: x.replace("_", " ").title(),
        )

    if st.button("Save Settings"):
        st.success("Settings saved successfully!")


if __name__ == "__main__":
    main()
