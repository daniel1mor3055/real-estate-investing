"""Input form components for Streamlit app."""

from typing import Any, Dict, List, Optional, Tuple
import streamlit as st

from ....core.models import PropertyType, FinancingType, IsraeliMortgageTrack
from ....adapters.config_loader import get_config_value


def _render_dual_input_widget(
    label: str,
    base_amount: float,
    default_percentage: float,
    key_prefix: str,
    min_percentage: int = 0,
    max_percentage: int = 100,
    percentage_step: int = 1,
    show_progress_bar: bool = True,
    currency_symbol: str = "$",
    help_text: str = "",
) -> Tuple[float, float]:
    """Render a dual-input widget that allows percentage or absolute amount input.
    
    Args:
        label: Display label for the widget
        base_amount: The base amount to calculate percentages from (e.g., purchase price)
        default_percentage: Default percentage value
        key_prefix: Unique prefix for widget keys
        min_percentage: Minimum percentage value
        max_percentage: Maximum percentage value
        percentage_step: Step size for percentage slider
        show_progress_bar: Whether to show visual progress bar
        currency_symbol: Currency symbol to display
        help_text: Help text for the input
        
    Returns:
        Tuple of (percentage, absolute_amount)
    """
    # Initialize session state for input mode if not exists
    mode_key = f"{key_prefix}_input_mode"
    if mode_key not in st.session_state:
        st.session_state[mode_key] = "Percentage"
    
    # Handle edge case: base amount is 0
    if base_amount == 0:
        st.warning(f"Base amount is 0, cannot calculate {label}")
        return 0.0, 0.0
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        input_mode = st.radio(
            "Input as:",
            ["Percentage", "Amount"],
            key=mode_key,
            help="Toggle between percentage and absolute amount input",
        )
    
    with col2:
        st.markdown(f"**{label}**")
        if help_text:
            st.caption(help_text)
        
        if input_mode == "Percentage":
            percentage = st.slider(
                f"{label} %",
                min_percentage,
                max_percentage,
                int(default_percentage),
                step=percentage_step,
                key=f"{key_prefix}_pct_slider",
                label_visibility="collapsed",
            )
            amount = base_amount * (percentage / 100.0)
            st.caption(f"= {currency_symbol}{amount:,.2f}")
        else:  # Amount mode
            default_amount = base_amount * (default_percentage / 100.0)
            amount = st.number_input(
                f"{label} Amount",
                min_value=0.0,
                max_value=base_amount * (max_percentage / 100.0),
                value=default_amount,
                step=base_amount * 0.01,  # 1% steps
                key=f"{key_prefix}_amount_input",
                label_visibility="collapsed",
            )
            percentage = (amount / base_amount) * 100.0 if base_amount > 0 else 0
            st.caption(f"= {percentage:.1f}%")
        
        # Visual progress bar
        if show_progress_bar:
            clamped_percentage = min(max(percentage, 0), 100)
            st.progress(clamped_percentage / 100.0)
    
    return percentage, amount


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

    # Store key values in session state for use by other input functions
    st.session_state["purchase_price"] = purchase_price
    st.session_state["units"] = units
    
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
    config = st.session_state.get("loaded_config")
    
    # Get purchase price from property inputs if available
    purchase_price = st.session_state.get("purchase_price", 300000)
    
    financing_type = st.selectbox(
        "Financing Type",
        [t.value for t in FinancingType if t != FinancingType.CASH],
        format_func=lambda x: x.replace("_", " ").title(),
    )
    
    # Dual-input widget for down payment
    default_down_payment = get_config_value(config, "financing.down_payment_percent", 20)
    down_payment_pct, down_payment_amount = _render_dual_input_widget(
        label="Down Payment",
        base_amount=purchase_price,
        default_percentage=default_down_payment,
        key_prefix="simple_down_payment",
        help_text=f"Down payment on {purchase_price:,.0f} purchase price",
    )
    
    col1, col2 = st.columns(2)
    with col1:
        interest_rate = st.number_input(
            "Interest Rate %", min_value=0.0, value=7.0, step=0.25
        )
        loan_term = st.selectbox("Loan Term (years)", [15, 30], index=1)
    with col2:
        points = st.number_input("Loan Points", min_value=0.0, value=0.0, step=0.5)

    return {
        "mode": "simple",
        "financing_type": financing_type,
        "is_cash": False,
        "down_payment": down_payment_pct,
        "down_payment_amount": down_payment_amount,
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
    
    # Get purchase price from property inputs if available
    purchase_price = st.session_state.get("purchase_price", 3756000)
    
    # Determine currency symbol based on purchase price magnitude (rough heuristic)
    currency_symbol = "₪" if purchase_price > 1000000 else "$"
    
    # Dual-input widget for down payment
    default_down_payment = get_config_value(config, "financing.down_payment_percent", 20)
    down_payment_pct, down_payment_amount = _render_dual_input_widget(
        label="Down Payment",
        base_amount=purchase_price,
        default_percentage=default_down_payment,
        key_prefix="israeli_down_payment",
        currency_symbol=currency_symbol,
        help_text=f"Down payment on {currency_symbol}{purchase_price:,.0f} purchase price",
    )
    
    # Calculate loan amount
    loan_amount = purchase_price - down_payment_amount

    default_num_tracks = len(config_tracks) if config_tracks else 2
    num_tracks = st.selectbox(
        "Number of Tracks", [1, 2, 3], index=min(default_num_tracks - 1, 2)
    )

    tracks = []
    total_percentage = 0

    for i in range(num_tracks):
        track_config = config_tracks[i] if i < len(config_tracks) else {}
        track_data = _get_single_track_inputs(
            i, track_config, total_percentage, loan_amount, currency_symbol
        )
        tracks.append(track_data)
        total_percentage += track_data["percentage"]

    _display_regulatory_compliance(tracks, loan_amount, currency_symbol)

    return {
        "mode": "israeli",
        "financing_type": "conventional",
        "is_cash": False,
        "down_payment": down_payment_pct,
        "down_payment_amount": down_payment_amount,
        "loan_amount": loan_amount,
        "tracks": tracks,
    }


def _get_single_track_inputs(
    track_index: int, 
    track_config: Dict, 
    total_percentage: int, 
    loan_amount: float,
    currency_symbol: str = "$"
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

        col1, col2 = st.columns(2)

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
        
        with col2:
            # Dual-input for track percentage/amount
            default_percentage = track_config.get(
                "percentage", 33 if track_index < 2 else max(1, 100 - total_percentage)
            )
            track_percentage, track_amount = _render_dual_input_widget(
                label=f"Track {track_index + 1} Allocation",
                base_amount=loan_amount,
                default_percentage=default_percentage,
                key_prefix=f"track_{track_index}_allocation",
                min_percentage=1,
                max_percentage=100,
                currency_symbol=currency_symbol,
                help_text=f"Allocation of {currency_symbol}{loan_amount:,.0f} total loan",
            )
            percentage = track_percentage

        # Interest rate and loan term section
        col3, col4 = st.columns(2)
        
        with col3:
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

        with col4:
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
        "amount": track_amount,
        "base_rate": base_rate,
        "loan_term": loan_term,
        "bank_of_israel_rate": bank_of_israel_rate,
        "expected_cpi": expected_cpi,
    }


def _display_regulatory_compliance(
    tracks: List[Dict], loan_amount: float = 0, currency_symbol: str = "$"
) -> None:
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
    status_text = "Compliant ✅" if overall_compliant else "Non-Compliant ⚠️"

    st.markdown(
        f'<div class="compliance-status {status_class}">', unsafe_allow_html=True
    )
    st.markdown(f"**Regulatory Compliance: {status_text}**")

    col1, col2, col3 = st.columns(3)
    with col1:
        fixed_amount = loan_amount * fixed_rate_ratio if loan_amount > 0 else 0
        st.metric(
            "Fixed Rate Tracks", 
            f"{fixed_rate_ratio:.1%}", 
            f"{currency_symbol}{fixed_amount:,.0f}"
        )
        st.caption("Required: >=33.3%")
    with col2:
        prime_amount = loan_amount * prime_rate_ratio if loan_amount > 0 else 0
        st.metric(
            "Prime Rate Track", 
            f"{prime_rate_ratio:.1%}", 
            f"{currency_symbol}{prime_amount:,.0f}"
        )
        st.caption("Limit: <=66.7%")
    with col3:
        total_amount = sum(track.get("amount", 0) for track in tracks)
        st.metric(
            "Total Allocation", 
            f"{total_percentage:.1f}%", 
            f"{currency_symbol}{total_amount:,.0f}"
        )
        st.caption("Target: 100%")

    if not fixed_compliant:
        st.warning("⚠️ Fixed-rate tracks must be at least 33.3% of total mortgage")
    if not prime_compliant:
        st.warning("⚠️ Prime rate track cannot exceed 66.7% of total mortgage")
    if not percentage_compliant:
        st.warning(f"⚠️ Track percentages total {total_percentage:.1f}% (should be 100%)")

    st.markdown("</div>", unsafe_allow_html=True)


def get_income_inputs() -> Dict[str, Any]:
    """Get income input fields.
    
    Returns:
        Dictionary of income input values
    """
    st.subheader("Rental Income")

    config = st.session_state.get("loaded_config")

    # Get units from property inputs if available
    units = st.session_state.get("units", 1)
    
    monthly_rent = st.number_input(
        "Monthly Rent per Unit",
        value=get_config_value(config, "income.monthly_rent", 2500),
        step=50,
    )
    
    # Calculate Gross Potential Rent (GPR)
    gross_potential_rent = monthly_rent * units
    
    # Determine currency symbol based on rent magnitude
    currency_symbol = "₪" if monthly_rent > 5000 else "$"
    
    st.markdown("### Vacancy & Credit Loss")
    
    # Dual-input for vacancy rate
    default_vacancy = get_config_value(config, "income.vacancy_rate", 5)
    vacancy_rate_pct, vacancy_amount = _render_dual_input_widget(
        label="Vacancy Rate",
        base_amount=gross_potential_rent,
        default_percentage=default_vacancy,
        key_prefix="vacancy_rate",
        min_percentage=0,
        max_percentage=20,
        currency_symbol=currency_symbol,
        help_text=f"Vacancy loss on {currency_symbol}{gross_potential_rent:,.0f}/month GPR",
    )
    
    # Dual-input for credit loss
    default_credit_loss = get_config_value(config, "income.credit_loss", 1)
    credit_loss_pct, credit_loss_amount = _render_dual_input_widget(
        label="Credit Loss",
        base_amount=gross_potential_rent,
        default_percentage=default_credit_loss,
        key_prefix="credit_loss",
        min_percentage=0,
        max_percentage=10,
        currency_symbol=currency_symbol,
        help_text=f"Credit loss on {currency_symbol}{gross_potential_rent:,.0f}/month GPR",
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

    # Store key values in session state for use by expense inputs
    st.session_state["monthly_rent"] = monthly_rent
    st.session_state["vacancy_rate"] = vacancy_rate_pct
    st.session_state["credit_loss"] = credit_loss_pct
    
    return {
        "monthly_rent": monthly_rent,
        "vacancy_rate": vacancy_rate_pct,
        "vacancy_amount": vacancy_amount,
        "credit_loss": credit_loss_pct,
        "credit_loss_amount": credit_loss_amount,
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
    
    # Calculate Effective Gross Income (EGI) estimate for reference
    # Get income values from session state if available
    monthly_rent = st.session_state.get("monthly_rent", 2500)
    units = st.session_state.get("units", 1)
    vacancy_rate = st.session_state.get("vacancy_rate", 5)
    credit_loss = st.session_state.get("credit_loss", 1)
    
    gross_potential_rent = monthly_rent * units
    egi_monthly = gross_potential_rent * (1 - (vacancy_rate + credit_loss) / 100)
    
    # Determine currency symbol
    currency_symbol = "₪" if monthly_rent > 5000 else "$"
    
    # Dual-input for maintenance
    default_maintenance = get_config_value(config, "expenses.maintenance_percent", 5)
    maintenance_pct, maintenance_amount = _render_dual_input_widget(
        label="Maintenance",
        base_amount=egi_monthly,
        default_percentage=default_maintenance,
        key_prefix="maintenance_expense",
        min_percentage=0,
        max_percentage=20,
        currency_symbol=currency_symbol,
        help_text=f"Maintenance cost on {currency_symbol}{egi_monthly:,.0f}/month EGI",
    )
    
    # Dual-input for management
    default_management = get_config_value(config, "expenses.management_percent", 8)
    management_pct, management_amount = _render_dual_input_widget(
        label="Management",
        base_amount=egi_monthly,
        default_percentage=default_management,
        key_prefix="management_expense",
        min_percentage=0,
        max_percentage=15,
        currency_symbol=currency_symbol,
        help_text=f"Management fee on {currency_symbol}{egi_monthly:,.0f}/month EGI",
    )
    
    # Dual-input for CapEx
    default_capex = get_config_value(config, "expenses.capex_percent", 5)
    capex_pct, capex_amount = _render_dual_input_widget(
        label="CapEx Reserve",
        base_amount=egi_monthly,
        default_percentage=default_capex,
        key_prefix="capex_expense",
        min_percentage=0,
        max_percentage=20,
        currency_symbol=currency_symbol,
        help_text=f"CapEx reserve on {currency_symbol}{egi_monthly:,.0f}/month EGI",
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
        "maintenance": maintenance_pct,
        "maintenance_amount": maintenance_amount,
        "management": management_pct,
        "management_amount": management_amount,
        "capex": capex_pct,
        "capex_amount": capex_amount,
        "annual_increase": annual_increase,
    }
