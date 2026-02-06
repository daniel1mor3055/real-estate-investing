"""Input form components for Streamlit app."""

from typing import Any, Dict, List, Optional
import streamlit as st

from ....core.models import PropertyType, FinancingType, IsraeliMortgageTrack
from ....adapters.config_loader import get_config_value


def get_property_inputs() -> Dict[str, Any]:
    """Get property input fields.
    
    Returns:
        Dictionary of property input values
    """
    config = st.session_state.get("loaded_config")

    col1, col2 = st.columns(2)

    with col1:
        address = st.text_input(
            "Address",
            get_config_value(config, "property.address", "123 Investment Property Lane"),
        )
        property_type_default = get_config_value(config, "property.type", "single_family")
        property_type_options = [t.value for t in PropertyType]
        property_type_index = (
            property_type_options.index(property_type_default)
            if property_type_default in property_type_options
            else 0
        )

        property_type = st.selectbox(
            "Property Type",
            property_type_options,
            index=property_type_index,
            format_func=lambda x: x.replace("_", " ").title(),
        )
        purchase_price = st.number_input(
            "Purchase Price",
            value=get_config_value(config, "property.purchase_price", 300000),
            step=5000,
        )
        closing_costs = st.number_input(
            "Closing Costs",
            value=get_config_value(config, "property.closing_costs", 7500),
            step=500,
        )
        rehab_budget = st.number_input(
            "Rehab Budget",
            value=get_config_value(config, "property.rehab_budget", 15000),
            step=1000,
        )

    with col2:
        units = st.number_input(
            "Units",
            min_value=1,
            value=get_config_value(config, "property.units", 1),
        )
        bedrooms = st.number_input(
            "Bedrooms",
            min_value=0,
            value=get_config_value(config, "property.bedrooms", 3),
        )
        bathrooms = st.number_input(
            "Bathrooms",
            min_value=0.0,
            value=float(get_config_value(config, "property.bathrooms", 2.0)),
            step=0.5,
        )
        sqft = st.number_input(
            "Square Feet",
            min_value=0,
            value=get_config_value(config, "property.square_footage", 1500),
            step=50,
        )
        year_built = st.number_input(
            "Year Built",
            min_value=1800,
            max_value=2026,
            value=get_config_value(config, "property.year_built", 1990),
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


def get_financing_inputs() -> Dict[str, Any]:
    """Get financing input fields.
    
    Returns:
        Dictionary of financing input values
    """
    st.subheader("Financing Configuration")

    financing_mode = st.radio(
        "Financing Mode",
        ["Israeli Mortgage Tracks", "Simple Loan", "Cash Purchase"],
        index=0,
        help="Choose between Israeli multi-track mortgage, simple single loan, or all-cash purchase",
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
        return _get_simple_loan_inputs()
    else:
        return _get_israeli_mortgage_inputs()


def _get_simple_loan_inputs() -> Dict[str, Any]:
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


def _get_israeli_mortgage_inputs() -> Dict[str, Any]:
    """Get Israeli mortgage track inputs with regulatory compliance."""
    st.markdown("### Israeli Mortgage Tracks (מסלולים)")
    st.info(
        "Configure up to 3 mortgage tracks. Israeli regulations require at least 1/3 fixed-rate and max 2/3 prime rate."
    )

    config = st.session_state.get("loaded_config")
    config_tracks = get_config_value(config, "financing.israeli_mortgage_tracks", [])

    down_payment = st.slider(
        "Down Payment %",
        0,
        100,
        get_config_value(config, "financing.down_payment_percent", 20),
    )

    default_num_tracks = len(config_tracks) if config_tracks else 2
    num_tracks = st.selectbox(
        "Number of Tracks", [1, 2, 3], index=min(default_num_tracks - 1, 2)
    )

    tracks = []
    total_percentage = 0

    for i in range(num_tracks):
        track_config = config_tracks[i] if i < len(config_tracks) else {}
        track_data = _get_single_track_inputs(i, track_config, total_percentage)
        tracks.append(track_data)
        total_percentage += track_data["percentage"]

    _display_regulatory_compliance(tracks)

    return {
        "mode": "israeli",
        "financing_type": "conventional",
        "is_cash": False,
        "down_payment": down_payment,
        "tracks": tracks,
    }


def _get_single_track_inputs(
    track_index: int, track_config: Dict, total_percentage: int
) -> Dict[str, Any]:
    """Get inputs for a single mortgage track."""
    with st.container():
        st.markdown(
            '<div class="track-container">', unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="track-header">Track {track_index + 1}</div>',
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            track_name = st.text_input(
                "Track Name",
                value=track_config.get("name", f"Track {track_index + 1}"),
                key=f"track_name_{track_index}",
            )

            track_type_options = [t.value for t in IsraeliMortgageTrack]
            track_type_default = track_config.get(
                "track_type", "fixed_unlinked" if track_index == 0 else "prime_rate"
            )
            track_type_index = (
                track_type_options.index(track_type_default)
                if track_type_default in track_type_options
                else 0
            )

            track_type = st.selectbox(
                "Track Type",
                track_type_options,
                index=track_type_index,
                format_func=lambda x: {
                    "fixed_unlinked": 'Fixed Unlinked (קל"צ)',
                    "prime_rate": "Prime Rate (פריים)",
                    "fixed_rate_linked": "Fixed-Rate Linked (צמוד)",
                }.get(x, x),
                key=f"track_type_{track_index}",
            )

            percentage = st.slider(
                "Percentage of Loan",
                1,
                100,
                track_config.get(
                    "percentage", 33 if track_index < 2 else max(1, 100 - total_percentage)
                ),
                key=f"track_percentage_{track_index}",
            )

        with col2:
            default_base_rate = track_config.get(
                "base_rate",
                4.5
                if track_type == "fixed_unlinked"
                else 3.8
                if track_type == "fixed_rate_linked"
                else 4.0,
            )

            base_rate = st.number_input(
                "Base Interest Rate %",
                min_value=0.0,
                value=float(default_base_rate),
                step=0.1,
                key=f"track_rate_{track_index}",
            )

            loan_term_options = [3, 5, 10, 15, 20, 25, 26, 30]
            default_term = track_config.get("loan_term", 30)
            loan_term_index = (
                loan_term_options.index(default_term)
                if default_term in loan_term_options
                else len(loan_term_options) - 1
            )

            loan_term = st.selectbox(
                "Term (years)",
                loan_term_options,
                index=loan_term_index,
                key=f"track_term_{track_index}",
            )

        with col3:
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
                    key=f"track_boi_{track_index}",
                )
                prime_rate = bank_of_israel_rate + 1.5
                st.info(f"Prime Rate: {prime_rate:.2f}%")

            elif track_type == "fixed_rate_linked":
                default_cpi = track_config.get("expected_cpi", 2.5)
                expected_cpi = st.number_input(
                    "Expected CPI %",
                    min_value=-2.0,
                    max_value=10.0,
                    value=float(default_cpi),
                    step=0.1,
                    help="Expected annual CPI for principal adjustment",
                    key=f"track_cpi_{track_index}",
                )
                st.info("Principal will be adjusted for CPI over time")

            else:
                st.info("Most stable track - fixed rate and principal")

        st.markdown("</div>", unsafe_allow_html=True)

    return {
        "name": track_name,
        "track_type": track_type,
        "percentage": percentage,
        "base_rate": base_rate,
        "loan_term": loan_term,
        "bank_of_israel_rate": bank_of_israel_rate,
        "expected_cpi": expected_cpi,
    }


def _display_regulatory_compliance(tracks: List[Dict]) -> None:
    """Display Israeli mortgage regulatory compliance status."""
    if not tracks:
        return

    total_percentage = sum(track["percentage"] for track in tracks)

    fixed_rate_percentage = sum(
        track["percentage"]
        for track in tracks
        if track["track_type"] in ["fixed_unlinked", "fixed_rate_linked"]
    )
    prime_rate_percentage = sum(
        track["percentage"]
        for track in tracks
        if track["track_type"] == "prime_rate"
    )

    fixed_rate_ratio = fixed_rate_percentage / total_percentage if total_percentage > 0 else 0
    prime_rate_ratio = prime_rate_percentage / total_percentage if total_percentage > 0 else 0

    fixed_compliant = fixed_rate_ratio >= 1 / 3
    prime_compliant = prime_rate_ratio <= 2 / 3
    percentage_compliant = abs(total_percentage - 100) <= 1

    overall_compliant = fixed_compliant and prime_compliant and percentage_compliant
    status_class = "compliant" if overall_compliant else "non-compliant"
    status_text = "Compliant" if overall_compliant else "Non-Compliant"

    st.markdown(
        f'<div class="compliance-status {status_class}">', unsafe_allow_html=True
    )
    st.markdown(f"**Regulatory Compliance: {status_text}**")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Fixed Rate Tracks", f"{fixed_rate_ratio:.1%}", "Required: >=33.3%")
    with col2:
        st.metric("Prime Rate Track", f"{prime_rate_ratio:.1%}", "Limit: <=66.7%")
    with col3:
        st.metric("Total Allocation", f"{total_percentage}%", "Target: 100%")

    if not fixed_compliant:
        st.warning("Fixed-rate tracks must be at least 33.3% of total mortgage")
    if not prime_compliant:
        st.warning("Prime rate track cannot exceed 66.7% of total mortgage")
    if not percentage_compliant:
        st.warning(f"Track percentages total {total_percentage}% (should be 100%)")

    st.markdown("</div>", unsafe_allow_html=True)


def get_income_inputs() -> Dict[str, Any]:
    """Get income input fields.
    
    Returns:
        Dictionary of income input values
    """
    st.subheader("Rental Income")

    config = st.session_state.get("loaded_config")

    col1, col2 = st.columns(2)
    with col1:
        monthly_rent = st.number_input(
            "Monthly Rent per Unit",
            value=get_config_value(config, "income.monthly_rent", 2500),
            step=50,
        )
        vacancy_rate = st.slider(
            "Vacancy Rate %",
            0,
            20,
            get_config_value(config, "income.vacancy_rate", 5),
        )

    with col2:
        credit_loss = st.slider(
            "Credit Loss %",
            0,
            10,
            get_config_value(config, "income.credit_loss", 1),
        )
        annual_increase = st.number_input(
            "Annual Rent Increase %",
            value=float(get_config_value(config, "income.annual_increase", 3.0)),
            step=0.5,
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


def get_expenses_inputs() -> Dict[str, Any]:
    """Get expense input fields.
    
    Returns:
        Dictionary of expense input values
    """
    st.subheader("Fixed Expenses")

    config = st.session_state.get("loaded_config")

    col1, col2 = st.columns(2)
    with col1:
        property_tax = st.number_input(
            "Annual Property Tax",
            value=get_config_value(config, "expenses.property_tax", 3600),
            step=100,
        )
        insurance = st.number_input(
            "Annual Insurance",
            value=get_config_value(config, "expenses.insurance", 1200),
            step=100,
        )

    with col2:
        hoa = st.number_input(
            "Monthly HOA",
            value=get_config_value(config, "expenses.hoa", 0),
            step=25,
        )
        utilities = st.number_input(
            "Monthly Utilities (Landlord Paid)",
            value=get_config_value(config, "expenses.utilities", 0),
            step=25,
        )

    st.subheader("Variable Expenses (% of Income)")

    col1, col2, col3 = st.columns(3)
    with col1:
        maintenance = st.slider(
            "Maintenance %",
            0,
            20,
            get_config_value(config, "expenses.maintenance_percent", 5),
        )
    with col2:
        management = st.slider(
            "Management %",
            0,
            15,
            get_config_value(config, "expenses.management_percent", 8),
        )
    with col3:
        capex = st.slider(
            "CapEx Reserve %",
            0,
            20,
            get_config_value(config, "expenses.capex_percent", 5),
        )

    annual_increase = st.number_input(
        "Annual Expense Growth %",
        value=float(get_config_value(config, "expenses.annual_increase", 3.0)),
        step=0.5,
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
