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
    get_market_inputs,
)
from ..components.metrics import display_metrics_overview
from ..components.charts import (
    display_cash_flow_chart,
    display_proforma_chart,
    display_proforma_table,
    display_sensitivity_heatmap,
    display_scenario_comparison_chart,
    display_operating_metrics_timeseries,
    display_wealth_metrics_timeseries,
    display_roe_timeseries,
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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Property", "Financing", "Income", "Expenses", "Market", "Analysis"]
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
        market_inputs = get_market_inputs()

    with tab6:
        _render_analysis_tab(
            deal_service,
            analysis_service,
            property_inputs,
            financing_inputs,
            income_inputs,
            expenses_inputs,
            market_inputs,
        )

    # Save configuration section (after tabs)
    _render_save_config_section(
        config_loader,
        property_inputs,
        financing_inputs,
        income_inputs,
        expenses_inputs,
        market_inputs,
    )


def _render_config_management(config_loader: ConfigLoader):
    """Render configuration management controls."""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    # Get all available configs dynamically from deals/ directory
    available_configs = config_loader.list_available_configs()
    
    # Prepend Manual option
    dropdown_options = ["Manual"] + available_configs
    
    # Set default to "Itzhak Navon 21" if available, otherwise "Manual"
    default_index = 0
    if "Itzhak Navon 21" in available_configs:
        default_index = dropdown_options.index("Itzhak Navon 21")
    
    with col1:
        config_file = st.selectbox(
            "Load Configuration",
            dropdown_options,
            index=default_index,
        )
    with col2:
        if st.button("Load Config"):
            if config_file != "Manual":
                try:
                    config_loaded = config_loader.load_configuration(config_file)
                    if config_loaded:
                        st.session_state["loaded_config"] = config_loaded
                        if "current_deal" in st.session_state:
                            del st.session_state["current_deal"]
                        st.success(f"Loaded configuration: {config_file}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error loading config: {e}")
    with col3:
        if st.button("Clear Config"):
            if "loaded_config" in st.session_state:
                del st.session_state["loaded_config"]
                if "current_deal" in st.session_state:
                    del st.session_state["current_deal"]
                st.success("Configuration cleared")
                st.rerun()


def _render_save_config_section(
    config_loader: ConfigLoader,
    property_inputs: dict,
    financing_inputs: dict,
    income_inputs: dict,
    expenses_inputs: dict,
    market_inputs: dict,
):
    """Render save configuration section."""
    st.divider()
    st.subheader("Save Configuration")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        config_name = st.text_input(
            "Configuration Name",
            placeholder="e.g., 'My Property Deal' or 'Oak Street Investment'",
            help="Enter a name for this configuration. It will be saved to the deals/ directory.",
        )
    
    with col2:
        st.write("")  # Spacer to align button
        st.write("")  # Spacer to align button
        if st.button("Save Config", type="primary"):
            if not config_name or config_name.strip() == "":
                st.error("Please enter a configuration name")
            else:
                try:
                    # Build configuration dictionary matching the JSON structure
                    config_data = {
                        "name": config_name,
                        "property": {
                            "address": property_inputs.get("address"),
                            "type": property_inputs.get("type"),
                            "purchase_price": property_inputs.get("purchase_price"),
                            "closing_costs": property_inputs.get("closing_costs"),
                            "rehab_budget": property_inputs.get("rehab_budget"),
                            "units": property_inputs.get("units"),
                            "bedrooms": property_inputs.get("bedrooms"),
                            "bathrooms": property_inputs.get("bathrooms"),
                            "square_footage": property_inputs.get("square_footage"),
                            "year_built": property_inputs.get("year_built"),
                        },
                        "financing": {
                            "type": financing_inputs.get("type"),
                            "cash_purchase": financing_inputs.get("cash_purchase"),
                            "down_payment_percent": financing_inputs.get("down_payment_percent"),
                            "interest_rate": financing_inputs.get("interest_rate"),
                            "loan_term": financing_inputs.get("loan_term"),
                            "points": financing_inputs.get("points"),
                        },
                        "income": {
                            "monthly_rent": income_inputs.get("monthly_rent"),
                            "vacancy_rate": income_inputs.get("vacancy_rate"),
                            "credit_loss": income_inputs.get("credit_loss"),
                            "annual_increase": income_inputs.get("annual_increase"),
                            "other_income": income_inputs.get("other_income", []),
                        },
                        "expenses": {
                            "property_tax": expenses_inputs.get("property_tax"),
                            "insurance": expenses_inputs.get("insurance"),
                            "hoa": expenses_inputs.get("hoa"),
                            "utilities": expenses_inputs.get("utilities"),
                            "maintenance_percent": expenses_inputs.get("maintenance_percent"),
                            "management_percent": expenses_inputs.get("management_percent"),
                            "capex_percent": expenses_inputs.get("capex_percent"),
                            "annual_increase": expenses_inputs.get("annual_increase"),
                        },
                    }
                    
                    # Add Israeli mortgage tracks if present
                    if "israeli_tracks" in financing_inputs:
                        config_data["financing"]["israeli_tracks"] = financing_inputs["israeli_tracks"]
                    
                    # Add market assumptions
                    config_data["market"] = {
                        "appreciation": market_inputs.get("appreciation", 3.5),
                        "sales_expense": market_inputs.get("sales_expense", 7.0),
                        "inflation": market_inputs.get("inflation", 2.5),
                    }
                    
                    # Save the configuration
                    saved_path = config_loader.save_configuration(config_name, config_data)
                    st.success(f"Configuration saved to: {saved_path}")
                    
                except Exception as e:
                    st.error(f"Error saving configuration: {e}")


def _render_analysis_tab(
    deal_service: DealService,
    analysis_service: AnalysisService,
    property_inputs: dict,
    financing_inputs: dict,
    income_inputs: dict,
    expenses_inputs: dict,
    market_inputs: dict,
):
    """Render the analysis tab with parameters and results."""
    config = st.session_state.get("loaded_config")

    col1, col2 = st.columns(2)
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
        show_details = st.checkbox("Show Detailed Breakdown", value=True)

    if st.button("Run Analysis", type="primary"):
        # Create deal using service
        deal = deal_service.create_deal_from_inputs(
            property_inputs,
            financing_inputs,
            income_inputs,
            expenses_inputs,
            market_inputs,
        )

        # Store in session state so results persist across widget interactions
        st.session_state["current_deal"] = deal

        # Run and display analysis
        _display_analysis_results(
            deal_service,
            analysis_service,
            deal,
            holding_period,
            show_details,
        )
    elif "current_deal" in st.session_state:
        # Re-display analysis when user interacts with widgets (e.g. sensitivity sliders)
        # Without this, moving sliders triggers a rerun and the analysis tabs would disappear
        deal = st.session_state["current_deal"]
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
    show_details: bool,
):
    """Display analysis results."""
    st.success("Analysis Complete!")

    # Run analysis
    try:
        result = deal_service.run_analysis(
            deal,
            holding_period=holding_period,
            include_proforma=True,
        )
    except Exception as e:
        st.error(f"Error running analysis: {e}")
        return

    metrics = result.metrics

    # Display tabs - Visualizations moved to second position
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Visualizations", "Cash Flow", "Pro Forma", "Sensitivity"]
    )

    with tab1:
        display_metrics_overview(deal, metrics)

    with tab2:
        st.subheader("Investment Performance Visualizations")
        
        # Time Series Charts Section
        with st.expander("📈 Time Series Analysis", expanded=True):
            st.markdown("### Operating Metrics Trends")
            st.markdown("Track how your core operating metrics evolve over the holding period.")
            display_operating_metrics_timeseries(deal, holding_period)
            
            st.markdown("### Return on Equity (ROE) Trends")
            st.markdown("Monitor equity efficiency and identify optimal exit timing.")
            display_roe_timeseries(deal, holding_period)
            
            st.markdown("### Wealth Building Trends")
            st.markdown("Visualize equity buildup and property value appreciation over time.")
            display_wealth_metrics_timeseries(deal, holding_period)
        
        # Legacy Charts Section
        with st.expander("📊 Additional Charts", expanded=False):
            st.markdown("### Equity & Cash Flow Breakdown")
            display_proforma_chart(deal, holding_period)

    with tab3:
        _display_cash_flow_analysis(deal)

    with tab4:
        display_proforma_table(deal, holding_period)

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
            key="sensitivity_var1",
        )
        var1_range = st.slider(
            f"{var1.replace('_', ' ').title()} Range (%)",
            -20,
            20,
            (-10, 10),
            key="sensitivity_var1_range",
        )

    with col2:
        var2 = st.selectbox(
            "Variable 2",
            ["purchase_price", "rent", "vacancy_rate", "interest_rate", "appreciation"],
            index=1,
            format_func=lambda x: x.replace("_", " ").title(),
            key="sensitivity_var2",
        )
        var2_range = st.slider(
            f"{var2.replace('_', ' ').title()} Range (%)",
            -20,
            20,
            (-10, 10),
            key="sensitivity_var2_range",
        )

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
