#!/usr/bin/env python3
"""Streamlit GUI for Real Estate Investment Analysis."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import os
from pathlib import Path

from src.models import (
    Property,
    PropertyType,
    Financing,
    FinancingType,
    SubLoan,
    IsraeliMortgageTrack,
    OperatingExpenses,
    ExpenseCategory,
    Income,
    IncomeSource,
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


def load_configuration(config_name: str):
    """Load a configuration file by name."""
    if config_name == "None (Manual Input)":
        return None
    
    # Map config names to file paths
    config_files = {
        "Itzhak Navon 21": "itzhak_navon_21.json",
        "Sample Deal": "sample_deal.json",
    }
    
    if config_name not in config_files:
        return None
    
    config_path = Path(config_files[config_name])
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return config_data
        else:
            st.error(f"Configuration file not found: {config_path}")
            return None
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        return None


def get_config_value(config_dict, key_path, default=None):
    """Get a value from nested config dictionary using dot notation."""
    if config_dict is None:
        return default
    
    keys = key_path.split('.')
    value = config_dict
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def main():
    """Main application entry point."""
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

    if page == "Detailed Analysis":
        detailed_analysis_page()
    elif page == "Portfolio Comparison":
        portfolio_comparison_page()
    elif page == "Market Research":
        market_research_page()
    elif page == "Settings":
        settings_page()


def detailed_analysis_page():
    """Detailed analysis with all inputs."""
    st.header("Detailed Property Analysis")
    
    # Configuration management
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        config_file = st.selectbox(
            "Load Configuration",
            ["None (Manual Input)", "Itzhak Navon 21", "Sample Deal", "Custom..."],
        )
    with col2:
        if st.button("Load Config"):
            config_loaded = load_configuration(config_file)
            if config_loaded:
                st.session_state["loaded_config"] = config_loaded
                st.success(f"Loaded configuration: {config_file}")
                st.rerun()
    with col3:
        if st.button("Clear Config"):
            if "loaded_config" in st.session_state:
                del st.session_state["loaded_config"]
                st.success("Configuration cleared")
                st.rerun()

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
        # Analysis parameters - available before running analysis
        config = st.session_state.get("loaded_config")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            holding_period_options = [5, 10, 15, 20, 30]
            default_holding = get_config_value(config, "analysis_defaults.holding_period", 10)
            holding_period_index = holding_period_options.index(default_holding) if default_holding in holding_period_options else 1
            
            holding_period = st.selectbox(
                "Holding Period (years)", 
                holding_period_options, 
                index=holding_period_index
            )
        with col2:
            investor_profiles = ["cash_flow", "balanced", "appreciation"]
            default_profile = get_config_value(config, "analysis_defaults.investor_profile", "balanced")
            profile_index = investor_profiles.index(default_profile) if default_profile in investor_profiles else 1
            
            investor_profile = st.selectbox(
                "Investor Profile",
                investor_profiles,
                index=profile_index,
                format_func=lambda x: x.replace("_", " ").title(),
            )
        with col3:
            show_details = st.checkbox("Show Detailed Breakdown", value=True)

        if st.button("Run Analysis", type="primary"):
            # Create deal
            deal = create_detailed_deal(
                property_inputs, financing_inputs, income_inputs, expenses_inputs
            )

            # Store in session state
            st.session_state["current_deal"] = deal

            # Run analysis with selected parameters
            run_detailed_analysis(deal, holding_period, investor_profile, show_details)


def get_property_inputs():
    """Get property input fields."""
    config = st.session_state.get("loaded_config")
    
    col1, col2 = st.columns(2)

    with col1:
        address = st.text_input(
            "Address", 
            get_config_value(config, "property.address", "123 Investment Property Lane")
        )
        property_type_default = get_config_value(config, "property.type", "single_family")
        property_type_options = [t.value for t in PropertyType]
        property_type_index = property_type_options.index(property_type_default) if property_type_default in property_type_options else 0
        
        property_type = st.selectbox(
            "Property Type",
            property_type_options,
            index=property_type_index,
            format_func=lambda x: x.replace("_", " ").title(),
        )
        purchase_price = st.number_input(
            "Purchase Price", 
            value=get_config_value(config, "property.purchase_price", 300000), 
            step=5000
        )
        closing_costs = st.number_input(
            "Closing Costs", 
            value=get_config_value(config, "property.closing_costs", 7500), 
            step=500
        )
        rehab_budget = st.number_input(
            "Rehab Budget", 
            value=get_config_value(config, "property.rehab_budget", 15000), 
            step=1000
        )

    with col2:
        units = st.number_input(
            "Units", 
            min_value=1, 
            value=get_config_value(config, "property.units", 1)
        )
        bedrooms = st.number_input(
            "Bedrooms", 
            min_value=0, 
            value=get_config_value(config, "property.bedrooms", 3)
        )
        bathrooms = st.number_input(
            "Bathrooms", 
            min_value=0.0, 
            value=float(get_config_value(config, "property.bathrooms", 2.0)), 
            step=0.5
        )
        sqft = st.number_input(
            "Square Feet", 
            min_value=0, 
            value=get_config_value(config, "property.square_footage", 1500), 
            step=50
        )
        year_built = st.number_input(
            "Year Built", 
            min_value=1800, 
            max_value=2026, 
            value=get_config_value(config, "property.year_built", 1990)
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
    st.subheader("Financing Configuration")

    # Financing mode selection
    financing_mode = st.radio(
        "Financing Mode",
        ["Simple Loan", "Israeli Mortgage Tracks", "Cash Purchase"],
        help="Choose between simple single loan, Israeli multi-track mortgage, or all-cash purchase",
    )

    if financing_mode == "Cash Purchase":
        return {
            "mode": "cash",
            "financing_type": "cash",
            "is_cash": True,
            "down_payment": 100,
            "tracks": [],
        }

    elif financing_mode == "Simple Loan":
        return get_simple_loan_inputs()

    else:  # Israeli Mortgage Tracks
        return get_israeli_mortgage_inputs()


def get_simple_loan_inputs():
    """Get simple single loan inputs."""
    col1, col2 = st.columns(2)

    with col1:
        financing_type = st.selectbox(
            "Financing Type",
            [t.value for t in FinancingType if t != FinancingType.CASH],
            format_func=lambda x: x.replace("_", " ").title(),
        )
        down_payment = st.slider("Down Payment %", 0, 100, 20)

    with col2:
        interest_rate = st.number_input(
            "Interest Rate %", min_value=0.0, value=7.0, step=0.25
        )
        loan_term = st.selectbox("Loan Term (years)", [15, 30], index=1)
        points = st.number_input("Loan Points", min_value=0.0, value=0.0, step=0.5)

    return {
        "mode": "simple",
        "financing_type": financing_type,
        "is_cash": False,
        "down_payment": down_payment,
        "interest_rate": interest_rate,
        "loan_term": loan_term,
        "points": points,
        "tracks": [],
    }


def get_israeli_mortgage_inputs():
    """Get Israeli mortgage track inputs with regulatory compliance."""
    st.markdown("### Israeli Mortgage Tracks (מסלולים)")
    st.info(
        "Configure up to 3 mortgage tracks. Israeli regulations require at least 1/3 fixed-rate and max 2/3 prime rate."
    )
    
    config = st.session_state.get("loaded_config")
    config_tracks = get_config_value(config, "financing.israeli_mortgage_tracks", [])

    # Down payment
    down_payment = st.slider(
        "Down Payment %", 
        0, 
        100, 
        get_config_value(config, "financing.down_payment_percent", 20)
    )

    # Number of tracks
    default_num_tracks = len(config_tracks) if config_tracks else 2
    num_tracks = st.selectbox("Number of Tracks", [1, 2, 3], index=min(default_num_tracks - 1, 2))

    tracks = []
    total_percentage = 0

    for i in range(num_tracks):
        # Get config for this track if available
        track_config = config_tracks[i] if i < len(config_tracks) else {}
        
        with st.container():
            st.markdown('<div class="track-container">', unsafe_allow_html=True)
            st.markdown(
                '<div class="track-header">Track {}</div>'.format(i + 1),
                unsafe_allow_html=True,
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                track_name = st.text_input(
                    "Track Name",
                    value=track_config.get("name", "Track {}".format(i + 1)),
                    key="track_name_{}".format(i),
                )

                track_type_options = [t.value for t in IsraeliMortgageTrack]
                track_type_default = track_config.get("track_type", "fixed_unlinked" if i == 0 else "prime_rate")
                track_type_index = track_type_options.index(track_type_default) if track_type_default in track_type_options else 0
                
                track_type = st.selectbox(
                    "Track Type",
                    track_type_options,
                    index=track_type_index,
                    format_func=lambda x: {
                        "fixed_unlinked": 'Fixed Unlinked (קל"צ)',
                        "prime_rate": "Prime Rate (פריים)",
                        "fixed_rate_linked": "Fixed-Rate Linked (צמוד)",
                    }.get(x, x),
                    key="track_type_{}".format(i),
                )

                percentage = st.slider(
                    "Percentage of Loan",
                    1,
                    100,
                    track_config.get("percentage", 33 if i < 2 else max(1, 100 - total_percentage)),
                    key="track_percentage_{}".format(i),
                )
                total_percentage += percentage

            with col2:
                default_base_rate = track_config.get("base_rate", 
                    4.5 if track_type == "fixed_unlinked"
                    else 3.8 if track_type == "fixed_rate_linked" else 4.0
                )
                
                base_rate = st.number_input(
                    "Base Interest Rate %",
                    min_value=0.0,
                    value=float(default_base_rate),
                    step=0.1,
                    key="track_rate_{}".format(i),
                )

                loan_term_options = [3, 5, 10, 15, 20, 25, 26, 30]
                default_term = track_config.get("loan_term", 30)
                loan_term_index = loan_term_options.index(default_term) if default_term in loan_term_options else len(loan_term_options) - 1
                
                loan_term = st.selectbox(
                    "Term (years)",
                    loan_term_options,
                    index=loan_term_index,
                    key="track_term_{}".format(i),
                )

            with col3:
                # Track-specific parameters
                bank_of_israel_rate = None
                expected_cpi = None

                if track_type == "prime_rate":
                    default_boi_rate = track_config.get("bank_of_israel_rate", 3.25)
                    bank_of_israel_rate = st.number_input(
                        "Bank of Israel Rate %",
                        min_value=0.0,
                        value=float(default_boi_rate),
                        step=0.25,
                        help="Official BoI rate (Prime = BoI + 1.5%)",
                        key="track_boi_{}".format(i),
                    )
                    # Calculate effective prime rate
                    # Prime = BoI + 1.5%, then subtract any track discount
                    prime_rate = bank_of_israel_rate + 1.5
                    track_discount = track_config.get("track_discount", 0)
                    effective_rate = prime_rate - track_discount
                    
                    st.info("Prime Rate: {:.2f}%".format(prime_rate))
                    if track_discount > 0:
                        st.info("After discount: {:.2f}%".format(effective_rate))

                elif track_type == "fixed_rate_linked":
                    default_cpi = track_config.get("expected_cpi", 2.5)
                    expected_cpi = st.number_input(
                        "Expected CPI %",
                        min_value=-2.0,
                        max_value=10.0,
                        value=float(default_cpi),
                        step=0.1,
                        help="Expected annual CPI for principal adjustment",
                        key="track_cpi_{}".format(i),
                    )
                    st.info("Principal will be adjusted for CPI over time")

                else:  # fixed_unlinked
                    st.info("Most stable track - fixed rate and principal")

            tracks.append(
                {
                    "name": track_name,
                    "track_type": track_type,
                    "percentage": percentage,
                    "base_rate": base_rate,
                    "loan_term": loan_term,
                    "bank_of_israel_rate": bank_of_israel_rate,
                    "expected_cpi": expected_cpi,
                }
            )

            st.markdown("</div>", unsafe_allow_html=True)

    # Regulatory compliance check
    display_regulatory_compliance(tracks)

    return {
        "mode": "israeli",
        "financing_type": "conventional",
        "is_cash": False,
        "down_payment": down_payment,
        "tracks": tracks,
    }


def get_income_inputs():
    """Get income input fields."""
    st.subheader("Rental Income")
    
    config = st.session_state.get("loaded_config")

    col1, col2 = st.columns(2)
    with col1:
        monthly_rent = st.number_input(
            "Monthly Rent per Unit", 
            value=get_config_value(config, "income.monthly_rent", 2500), 
            step=50
        )
        vacancy_rate = st.slider(
            "Vacancy Rate %", 
            0, 
            20, 
            get_config_value(config, "income.vacancy_rate", 5)
        )

    with col2:
        credit_loss = st.slider(
            "Credit Loss %", 
            0, 
            10, 
            get_config_value(config, "income.credit_loss", 1)
        )
        annual_increase = st.number_input(
            "Annual Rent Increase %", 
            value=float(get_config_value(config, "income.annual_increase", 3.0)), 
            step=0.5
        )

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
    
    config = st.session_state.get("loaded_config")

    col1, col2 = st.columns(2)
    with col1:
        property_tax = st.number_input(
            "Annual Property Tax", 
            value=get_config_value(config, "expenses.property_tax", 3600), 
            step=100
        )
        insurance = st.number_input(
            "Annual Insurance", 
            value=get_config_value(config, "expenses.insurance", 1200), 
            step=100
        )

    with col2:
        hoa = st.number_input(
            "Monthly HOA", 
            value=get_config_value(config, "expenses.hoa", 0), 
            step=25
        )
        utilities = st.number_input(
            "Monthly Utilities (Landlord Paid)", 
            value=get_config_value(config, "expenses.utilities", 0), 
            step=25
        )

    st.subheader("Variable Expenses (% of Income)")

    col1, col2, col3 = st.columns(3)
    with col1:
        maintenance = st.slider(
            "Maintenance %", 
            0, 
            20, 
            get_config_value(config, "expenses.maintenance_percent", 5)
        )
    with col2:
        management = st.slider(
            "Management %", 
            0, 
            15, 
            get_config_value(config, "expenses.management_percent", 8)
        )
    with col3:
        capex = st.slider(
            "CapEx Reserve %", 
            0, 
            20, 
            get_config_value(config, "expenses.capex_percent", 5)
        )

    annual_increase = st.number_input(
        "Annual Expense Growth %", 
        value=float(get_config_value(config, "expenses.annual_increase", 3.0)), 
        step=0.5
    )

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


def display_regulatory_compliance(tracks):
    """Display Israeli mortgage regulatory compliance status."""
    if not tracks:
        return

    total_percentage = sum(track["percentage"] for track in tracks)

    # Calculate compliance ratios
    fixed_rate_percentage = sum(
        track["percentage"]
        for track in tracks
        if track["track_type"] in ["fixed_unlinked", "fixed_rate_linked"]
    )
    prime_rate_percentage = sum(
        track["percentage"] for track in tracks if track["track_type"] == "prime_rate"
    )

    fixed_rate_ratio = (
        fixed_rate_percentage / total_percentage if total_percentage > 0 else 0
    )
    prime_rate_ratio = (
        prime_rate_percentage / total_percentage if total_percentage > 0 else 0
    )

    # Check compliance
    fixed_compliant = fixed_rate_ratio >= 1 / 3
    prime_compliant = prime_rate_ratio <= 2 / 3
    percentage_compliant = abs(total_percentage - 100) <= 1  # Allow 1% tolerance

    overall_compliant = fixed_compliant and prime_compliant and percentage_compliant

    # Display status
    status_class = "compliant" if overall_compliant else "non-compliant"
    status_text = "✅ Compliant" if overall_compliant else "❌ Non-Compliant"

    st.markdown(
        '<div class="compliance-status {}">'.format(status_class),
        unsafe_allow_html=True,
    )
    st.markdown("**Regulatory Compliance: {}**".format(status_text))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Fixed Rate Tracks", "{:.1f}%".format(fixed_rate_ratio), "Required: ≥33.3%"
        )
    with col2:
        st.metric(
            "Prime Rate Track", "{:.1f}%".format(prime_rate_ratio), "Limit: ≤66.7%"
        )
    with col3:
        st.metric("Total Allocation", "{}%".format(total_percentage), "Target: 100%")

    # Warnings
    if not fixed_compliant:
        st.warning("⚠️ Fixed-rate tracks must be at least 33.3% of total mortgage")
    if not prime_compliant:
        st.warning("⚠️ Prime rate track cannot exceed 66.7% of total mortgage")
    if not percentage_compliant:
        st.warning(
            "⚠️ Track percentages total {}% (should be 100%)".format(total_percentage)
        )

    st.markdown("</div>", unsafe_allow_html=True)


def create_detailed_deal(prop, fin, inc, exp):
    """Create a deal object from detailed inputs."""
    property = Property(
        address=prop["address"],
        property_type=PropertyType(prop["property_type"]),
        purchase_price=prop["purchase_price"],
        closing_costs=prop["closing_costs"],
        rehab_budget=prop.get("rehab_budget", 0),
        num_units=prop["units"],
        bedrooms=prop["bedrooms"],
        bathrooms=prop["bathrooms"],
        square_footage=prop.get("sqft", prop.get("square_feet", 0)),
        year_built=prop["year_built"],
    )

    # Create financing based on mode
    if fin.get("mode") == "cash":
        financing = Financing(
            financing_type=FinancingType.CASH,
            is_cash_purchase=True,
            down_payment_percent=100,
            interest_rate=0,
            loan_term_years=30,
            loan_points=0,
        )
    elif fin.get("mode") == "israeli" and fin.get("tracks"):
        # Create Israeli mortgage with multiple tracks
        sub_loans = []
        purchase_price = property.purchase_price
        loan_amount = purchase_price * (1 - fin["down_payment"] / 100)

        for track_data in fin["tracks"]:
            track_loan_amount = loan_amount * (track_data["percentage"] / 100)

            # Create SubLoan based on track type
            sub_loan = SubLoan(
                name=track_data["name"],
                track_type=IsraeliMortgageTrack(track_data["track_type"]),
                loan_amount=track_loan_amount,
                base_interest_rate=track_data["base_rate"],
                loan_term_years=track_data["loan_term"],
                bank_of_israel_rate=track_data.get("bank_of_israel_rate"),
                expected_cpi=track_data.get("expected_cpi"),
            )
            sub_loans.append(sub_loan)

        financing = Financing.create_israeli_mortgage(
            financing_type=FinancingType(fin["financing_type"]),
            down_payment_percent=fin["down_payment"],
            mortgage_tracks=sub_loans,
        )
    else:
        # Simple loan (backward compatibility)
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
        market_assumptions=MarketAssumptions(),
        deal_status=DealStatus.ANALYZING,
    )


def run_detailed_analysis(deal, holding_period, investor_profile, show_details):
    """Run and display detailed analysis."""
    st.success("Analysis Complete!")

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
            go.Heatmap(
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
    
    # Load current config if available
    config = st.session_state.get("loaded_config")
    
    # Display current configuration info if loaded
    if config:
        st.info(f"Current Configuration: {config.get('name', 'Unknown')}")
        st.markdown(f"**Property:** {get_config_value(config, 'property.address', 'N/A')}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Income Defaults**")
        default_vacancy = st.number_input(
            "Default Vacancy Rate %", 
            value=float(get_config_value(config, "analysis_defaults.default_vacancy_rate", 5.0))
        )
        default_rent_growth = st.number_input(
            "Default Rent Growth %", 
            value=float(get_config_value(config, "analysis_defaults.default_rent_growth", 3.0))
        )

        st.markdown("**Expense Defaults**")
        default_maintenance = st.number_input(
            "Default Maintenance %", 
            value=float(get_config_value(config, "analysis_defaults.default_maintenance", 5.0))
        )
        default_management = st.number_input(
            "Default Management %", 
            value=float(get_config_value(config, "analysis_defaults.default_management", 8.0))
        )
        default_capex = st.number_input(
            "Default CapEx %", 
            value=float(get_config_value(config, "expenses.capex_percent", 5.0))
        )

    with col2:
        st.markdown("**Market Defaults**")
        default_appreciation = st.number_input(
            "Default Appreciation %", 
            value=float(get_config_value(config, "analysis_defaults.default_appreciation", 3.5))
        )
        default_inflation = st.number_input(
            "Default Inflation %", 
            value=float(get_config_value(config, "market.inflation", 2.5))
        )

        st.markdown("**Analysis Defaults**")
        holding_options = [5, 10, 15, 20, 30]
        default_holding_val = get_config_value(config, "analysis_defaults.holding_period", 10)
        holding_index = holding_options.index(default_holding_val) if default_holding_val in holding_options else 1
        
        default_holding = st.selectbox(
            "Default Holding Period", 
            holding_options, 
            index=holding_index
        )
        
        profile_options = ["cash_flow", "balanced", "appreciation"]
        default_profile_val = get_config_value(config, "analysis_defaults.investor_profile", "balanced")
        profile_index = profile_options.index(default_profile_val) if default_profile_val in profile_options else 1
        
        default_profile = st.selectbox(
            "Default Investor Profile",
            profile_options,
            index=profile_index,
            format_func=lambda x: x.replace("_", " ").title(),
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Settings"):
            # Update session state with new defaults
            if "settings" not in st.session_state:
                st.session_state["settings"] = {}
            
            st.session_state["settings"].update({
                "default_vacancy": default_vacancy,
                "default_rent_growth": default_rent_growth,
                "default_maintenance": default_maintenance,
                "default_management": default_management,
                "default_capex": default_capex,
                "default_appreciation": default_appreciation,
                "default_inflation": default_inflation,
                "default_holding": default_holding,
                "default_profile": default_profile,
            })
            
            st.success("Settings saved successfully!")
    
    with col2:
        if st.button("Reset to Defaults"):
            if "settings" in st.session_state:
                del st.session_state["settings"]
            if "loaded_config" in st.session_state:
                del st.session_state["loaded_config"]
            st.success("Settings reset to defaults!")
            st.rerun()


if __name__ == "__main__":
    main()
