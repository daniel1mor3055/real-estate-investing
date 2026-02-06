"""Detailed analysis page for Streamlit app."""

import streamlit as st
from datetime import datetime

from ....core.models import Deal, DealStatus, MarketAssumptions
from ....services.deal_service import DealService
from ....services.analysis_service import AnalysisService
from ....adapters.config_loader import ConfigLoader, get_config_value
from ..components.inputs import (
    get_property_inputs,
    get_financing_inputs,
    get_income_inputs,
    get_expenses_inputs,
)
from ..components.metrics import display_metrics_overview
from ..components.charts import (
    display_cash_flow_chart,
    display_proforma_chart,
    display_proforma_table,
    display_sensitivity_heatmap,
    display_scenario_comparison_chart,
)


def detailed_analysis_page():
    """Detailed analysis with all inputs."""
    st.header("Detailed Property Analysis")

    # Initialize services
    deal_service = DealService()
    analysis_service = AnalysisService()
    config_loader = ConfigLoader()

    # Configuration management
    _render_config_management(config_loader)

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
        _render_analysis_tab(
            deal_service,
            analysis_service,
            property_inputs,
            financing_inputs,
            income_inputs,
            expenses_inputs,
        )


def _render_config_management(config_loader: ConfigLoader):
    """Render configuration management controls."""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    available_configs = ["None (Manual Input)"] + config_loader.list_available_configs()
    
    with col1:
        config_file = st.selectbox(
            "Load Configuration",
            available_configs + ["Custom..."],
        )
    with col2:
        if st.button("Load Config"):
            if config_file not in ["None (Manual Input)", "Custom..."]:
                try:
                    config_loaded = config_loader.load_configuration(config_file)
                    if config_loaded:
                        st.session_state["loaded_config"] = config_loaded
                        st.success(f"Loaded configuration: {config_file}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error loading config: {e}")
    with col3:
        if st.button("Clear Config"):
            if "loaded_config" in st.session_state:
                del st.session_state["loaded_config"]
                st.success("Configuration cleared")
                st.rerun()


def _render_analysis_tab(
    deal_service: DealService,
    analysis_service: AnalysisService,
    property_inputs: dict,
    financing_inputs: dict,
    income_inputs: dict,
    expenses_inputs: dict,
):
    """Render the analysis tab with parameters and results."""
    config = st.session_state.get("loaded_config")

    col1, col2, col3 = st.columns(3)
    with col1:
        holding_period_options = [5, 10, 15, 20, 30]
        default_holding = get_config_value(config, "analysis_defaults.holding_period", 10)
        holding_period_index = (
            holding_period_options.index(default_holding)
            if default_holding in holding_period_options
            else 1
        )

        holding_period = st.selectbox(
            "Holding Period (years)",
            holding_period_options,
            index=holding_period_index,
        )
    with col2:
        investor_profiles = ["cash_flow", "balanced", "appreciation"]
        default_profile = get_config_value(
            config, "analysis_defaults.investor_profile", "balanced"
        )
        profile_index = (
            investor_profiles.index(default_profile)
            if default_profile in investor_profiles
            else 1
        )

        investor_profile = st.selectbox(
            "Investor Profile",
            investor_profiles,
            index=profile_index,
            format_func=lambda x: x.replace("_", " ").title(),
        )
    with col3:
        show_details = st.checkbox("Show Detailed Breakdown", value=True)

    if st.button("Run Analysis", type="primary"):
        # Create deal using service
        deal = deal_service.create_deal_from_inputs(
            property_inputs,
            financing_inputs,
            income_inputs,
            expenses_inputs,
        )

        # Store in session state
        st.session_state["current_deal"] = deal

        # Run and display analysis
        _display_analysis_results(
            deal_service,
            analysis_service,
            deal,
            holding_period,
            investor_profile,
            show_details,
        )


def _display_analysis_results(
    deal_service: DealService,
    analysis_service: AnalysisService,
    deal: Deal,
    holding_period: int,
    investor_profile: str,
    show_details: bool,
):
    """Display analysis results."""
    st.success("Analysis Complete!")

    # Run analysis
    try:
        result = deal_service.run_analysis(
            deal,
            holding_period=holding_period,
            investor_profile=investor_profile,
            include_proforma=True,
        )
    except Exception as e:
        st.error(f"Error running analysis: {e}")
        return

    metrics = result.metrics

    # Display tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Cash Flow", "Pro Forma", "Visualizations", "Sensitivity"]
    )

    with tab1:
        display_metrics_overview(deal, metrics)

    with tab2:
        _display_cash_flow_analysis(deal)

    with tab3:
        display_proforma_table(deal, holding_period)

    with tab4:
        display_proforma_chart(deal, holding_period)

    with tab5:
        _display_sensitivity_analysis(analysis_service, deal, holding_period)


def _display_cash_flow_analysis(deal: Deal):
    """Display detailed cash flow analysis."""
    st.subheader("Cash Flow Analysis")
    display_cash_flow_chart(deal, years=3)


def _display_sensitivity_analysis(
    analysis_service: AnalysisService,
    deal: Deal,
    holding_period: int,
):
    """Display sensitivity analysis controls and results."""
    st.subheader("Sensitivity Analysis")

    col1, col2 = st.columns(2)
    with col1:
        var1 = st.selectbox(
            "Variable 1",
            ["purchase_price", "rent", "vacancy_rate", "interest_rate", "appreciation"],
            index=0,
            format_func=lambda x: x.replace("_", " ").title(),
        )
        var1_range = st.slider(f"{var1.replace('_', ' ').title()} Range (%)", -20, 20, (-10, 10))

    with col2:
        var2 = st.selectbox(
            "Variable 2",
            ["purchase_price", "rent", "vacancy_rate", "interest_rate", "appreciation"],
            index=1,
            format_func=lambda x: x.replace("_", " ").title(),
        )
        var2_range = st.slider(f"{var2.replace('_', ' ').title()} Range (%)", -20, 20, (-10, 10))

    target_metric = st.selectbox(
        "Target Metric",
        ["irr", "coc_return", "cap_rate", "dscr", "cash_flow"],
        format_func=lambda x: x.replace("_", " ").upper(),
    )

    if st.button("Run Sensitivity Analysis"):
        with st.spinner("Running sensitivity analysis..."):
            try:
                result = analysis_service.run_sensitivity_analysis(
                    deal,
                    variable1=var1,
                    variable2=var2,
                    range1=var1_range,
                    range2=var2_range,
                    steps=10,
                    target_metric=target_metric,
                    holding_period=holding_period,
                )

                display_sensitivity_heatmap(
                    x_values=result.variable1_values,
                    y_values=result.variable2_values,
                    z_values=result.metric_grid,
                    x_label=var1.replace("_", " ").title(),
                    y_label=var2.replace("_", " ").title(),
                    title=f"{target_metric.upper()} Sensitivity: {var1} vs {var2}",
                )

                st.info(f"Base case {target_metric.upper()}: {result.base_value:.2%}" if target_metric in ["irr", "coc_return", "cap_rate"] else f"Base case {target_metric.upper()}: {result.base_value:.2f}")

            except Exception as e:
                st.error(f"Error running sensitivity analysis: {e}")

    # Scenario Analysis
    st.subheader("Scenario Analysis")

    if st.button("Run Scenario Analysis"):
        with st.spinner("Running scenario analysis..."):
            try:
                result = analysis_service.run_scenario_analysis(
                    deal,
                    holding_period=holding_period,
                )

                comparison = result.to_comparison_dict()
                display_scenario_comparison_chart(comparison)

                # Show table
                import pandas as pd
                df = pd.DataFrame(comparison).T
                df.index.name = "Scenario"
                
                # Format percentage columns
                for col in ["irr", "coc_return"]:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: f"{x:.2%}" if x else "N/A")
                for col in ["dscr", "equity_multiple"]:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: f"{x:.2f}" if x else "N/A")
                for col in ["noi_year1", "cash_flow_year1"]:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: f"${x:,.0f}" if x else "N/A")

                st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"Error running scenario analysis: {e}")
