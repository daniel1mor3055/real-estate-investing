"""Settings page for Streamlit app."""

import streamlit as st

from ....adapters.config_loader import get_config_value


def settings_page():
    """Settings page."""
    st.header("Settings")

    st.subheader("Default Assumptions")

    config = st.session_state.get("loaded_config")

    if config:
        st.info(f"Current Configuration: {config.get('name', 'Unknown')}")
        st.markdown(
            f"**Property:** {get_config_value(config, 'property.address', 'N/A')}"
        )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Income Defaults**")
        default_vacancy = st.number_input(
            "Default Vacancy Rate %",
            value=float(
                get_config_value(config, "analysis_defaults.default_vacancy_rate", 5.0)
            ),
        )
        default_rent_growth = st.number_input(
            "Default Rent Growth %",
            value=float(
                get_config_value(config, "analysis_defaults.default_rent_growth", 3.0)
            ),
        )

        st.markdown("**Expense Defaults**")
        default_maintenance = st.number_input(
            "Default Maintenance %",
            value=float(
                get_config_value(config, "analysis_defaults.default_maintenance", 5.0)
            ),
        )
        default_management = st.number_input(
            "Default Management %",
            value=float(
                get_config_value(config, "analysis_defaults.default_management", 8.0)
            ),
        )
        default_capex = st.number_input(
            "Default CapEx %",
            value=float(get_config_value(config, "expenses.capex_percent", 5.0)),
        )

    with col2:
        st.markdown("**Market Defaults**")
        default_appreciation = st.number_input(
            "Default Appreciation %",
            value=float(
                get_config_value(
                    config, "analysis_defaults.default_appreciation", 3.5
                )
            ),
        )
        default_inflation = st.number_input(
            "Default Inflation %",
            value=float(get_config_value(config, "market.inflation", 2.5)),
        )

        st.markdown("**Analysis Defaults**")
        holding_options = [5, 10, 15, 20, 30]
        default_holding_val = get_config_value(
            config, "analysis_defaults.holding_period", 10
        )
        holding_index = (
            holding_options.index(default_holding_val)
            if default_holding_val in holding_options
            else 1
        )

        default_holding = st.selectbox(
            "Default Holding Period",
            holding_options,
            index=holding_index,
        )

        profile_options = ["cash_flow", "balanced", "appreciation"]
        default_profile_val = get_config_value(
            config, "analysis_defaults.investor_profile", "balanced"
        )
        profile_index = (
            profile_options.index(default_profile_val)
            if default_profile_val in profile_options
            else 1
        )

        default_profile = st.selectbox(
            "Default Investor Profile",
            profile_options,
            index=profile_index,
            format_func=lambda x: x.replace("_", " ").title(),
        )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Settings"):
            if "settings" not in st.session_state:
                st.session_state["settings"] = {}

            st.session_state["settings"].update(
                {
                    "default_vacancy": default_vacancy,
                    "default_rent_growth": default_rent_growth,
                    "default_maintenance": default_maintenance,
                    "default_management": default_management,
                    "default_capex": default_capex,
                    "default_appreciation": default_appreciation,
                    "default_inflation": default_inflation,
                    "default_holding": default_holding,
                    "default_profile": default_profile,
                }
            )

            st.success("Settings saved successfully!")

    with col2:
        if st.button("Reset to Defaults"):
            if "settings" in st.session_state:
                del st.session_state["settings"]
            if "loaded_config" in st.session_state:
                del st.session_state["loaded_config"]
            st.success("Settings reset to defaults!")
            st.rerun()

    # About section
    st.divider()
    st.subheader("About")
    st.markdown("""
    **Real Estate Investment Analyzer**
    
    A professional-grade analysis tool for rental property investments.
    
    Features:
    - Detailed property analysis with customizable inputs
    - Israeli mortgage track support with regulatory compliance
    - Multi-year pro-forma projections
    - Sensitivity and scenario analysis
    - Multiple investor profile scoring
    
    Architecture:
    - Domain models with Pydantic validation
    - Strategy pattern for investor profiles
    - Calculator pattern for financial computations
    - Service layer for business logic coordination
    """)
