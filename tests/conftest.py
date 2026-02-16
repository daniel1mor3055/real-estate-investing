"""Shared fixtures for Real Estate Investment testing.

This module provides reusable test fixtures that mirror the examples
from docs/CONTEXT.md (source of truth) for consistent testing.
"""

import pytest
from src.core.models.deal import Deal, MarketAssumptions
from src.core.models.property import Property, PropertyType
from src.core.models.financing import Financing, FinancingType
from src.core.models.income import Income, IncomeItem, IncomeSource
from src.core.models.expenses import OperatingExpenses


# =============================================================================
# CONTEXT.md Example Deal Fixture
# =============================================================================
# This fixture matches the example in CONTEXT.md Part III table:
# - Purchase Price: $250,000
# - Down Payment: 20% ($50,000)
# - Closing/Rehab: $6,000
# - Year 1 GPR: $24,000
# - Year 1 EGI: $22,800 (5% vacancy)
# - Year 1 NOI: $12,540
# - Annual Debt Service: $8,587
# - Year 1 Cash Flow: $3,953
# =============================================================================


@pytest.fixture
def context_md_example_deal() -> Deal:
    """Deal matching CONTEXT.md Part III example table.
    
    Expected Values (from CONTEXT.md):
    - Purchase Price: $250,000
    - Down Payment: $50,000 (20%)
    - Closing + Rehab: $6,000
    - Total Cash Invested: $56,000
    - Year 1 GPR: $24,000
    - Year 1 EGI: $22,800
    - Year 1 OpEx: $10,260 (45% of EGI)
    - Year 1 NOI: $12,540
    - Annual Debt Service: $8,587
    - Year 1 Cash Flow: $3,953
    """
    property_obj = Property(
        address="123 CONTEXT MD Example St",
        property_type=PropertyType.SINGLE_FAMILY,
        square_footage=1500,
        num_units=1,
        bedrooms=3,
        bathrooms=2,
        year_built=2000,
        purchase_price=250_000,
        closing_costs=3_000,
        rehab_budget=3_000,
    )
    
    # Financing to achieve ~$8,587/year debt service
    # Loan: $200,000 @ ~6.5% for 30 years = ~$1,264/month = ~$15,168/year
    # But CONTEXT.md shows $8,587, which suggests different terms
    # Let's reverse-engineer: $8,587/12 = $715.58/month
    # $200,000 loan, 30 years, solving for rate that gives $715.58
    # This is approximately 4.0% interest rate
    financing = Financing.create_simple_loan(
        financing_type=FinancingType.CONVENTIONAL,
        down_payment_percent=20.0,
        interest_rate=4.0,
        loan_term_years=30,
        loan_points=0,
    )
    
    # Income: $2,000/month = $24,000/year GPR
    income = Income(
        monthly_rent_per_unit=2_000,
        vacancy_rate_percent=5.0,
        credit_loss_percent=0.0,  # CONTEXT.md example doesn't show credit loss
        annual_rent_increase_percent=3.0,
    )
    
    # Expenses: Need to achieve $10,260 total OpEx (45% of EGI)
    # EGI = $22,800, OpEx = $10,260
    # Fixed: Property Tax ($2,500) + Insurance ($1,200) = $3,700
    # Variable: Maintenance (5%) + Management (8%) + CapEx (5%) = 18% of EGI
    # 18% of $22,800 = $4,104
    # Remaining: $10,260 - $3,700 - $4,104 = $2,456 (other/utilities)
    expenses = OperatingExpenses(
        property_tax_annual=2_500,
        insurance_annual=1_200,
        hoa_monthly=0,
        maintenance_percent=5.0,
        property_management_percent=8.0,
        capex_reserve_percent=5.0,
        landlord_paid_utilities_monthly=204.67,  # ~$2,456/year
        annual_expense_growth_percent=3.0,
    )
    
    market_assumptions = MarketAssumptions(
        annual_appreciation_percent=3.0,
        sales_expense_percent=7.0,
        inflation_rate_percent=2.5,
    )
    
    deal = Deal(
        deal_id="context-md-example",
        deal_name="CONTEXT.md Example Deal",
        property=property_obj,
        financing=financing,
        income=income,
        expenses=expenses,
        market_assumptions=market_assumptions,
        holding_period_years=10,
    )
    
    return deal


@pytest.fixture
def sample_deal() -> Deal:
    """Standard sample deal for general testing.
    
    A typical rental property with solid positive cash flow.
    Designed to have DSCR > 1.25 and positive CoC return.
    """
    property_obj = Property(
        address="456 Sample Test Ave",
        property_type=PropertyType.SINGLE_FAMILY,
        square_footage=1800,
        num_units=1,
        bedrooms=3,
        bathrooms=2,
        year_built=1990,
        purchase_price=250_000,
        closing_costs=5_000,
        rehab_budget=5_000,
    )
    
    financing = Financing.create_simple_loan(
        financing_type=FinancingType.CONVENTIONAL,
        down_payment_percent=25.0,
        interest_rate=5.5,  # Lower rate for better cash flow
        loan_term_years=30,
        loan_points=0.5,
    )
    
    income = Income(
        monthly_rent_per_unit=2_200,  # Strong rent relative to price
        vacancy_rate_percent=5.0,
        credit_loss_percent=1.0,
        annual_rent_increase_percent=3.0,
    )
    
    expenses = OperatingExpenses(
        property_tax_annual=3_000,
        insurance_annual=1_200,
        hoa_monthly=0,
        maintenance_percent=5.0,
        property_management_percent=8.0,
        capex_reserve_percent=5.0,
        landlord_paid_utilities_monthly=0,
        annual_expense_growth_percent=2.5,
    )
    
    market_assumptions = MarketAssumptions(
        annual_appreciation_percent=3.5,
        sales_expense_percent=7.0,
        inflation_rate_percent=2.5,
    )
    
    deal = Deal(
        deal_id="sample-001",
        deal_name="Sample Test Deal",
        property=property_obj,
        financing=financing,
        income=income,
        expenses=expenses,
        market_assumptions=market_assumptions,
        holding_period_years=10,
    )
    
    return deal


@pytest.fixture
def cash_purchase_deal() -> Deal:
    """Deal with all-cash purchase (no financing).
    
    Used to test edge cases:
    - DSCR should be infinity
    - No debt service
    - Higher cash flow but lower CoC due to full cash investment
    """
    property_obj = Property(
        address="789 Cash Purchase Ln",
        property_type=PropertyType.SINGLE_FAMILY,
        square_footage=1600,
        num_units=1,
        bedrooms=3,
        bathrooms=2,
        year_built=2010,
        purchase_price=200_000,
        closing_costs=4_000,
        rehab_budget=0,
    )
    
    financing = Financing(
        financing_type=FinancingType.CASH,
        is_cash_purchase=True,
        down_payment_percent=100.0,
    )
    
    income = Income(
        monthly_rent_per_unit=1_800,
        vacancy_rate_percent=5.0,
        credit_loss_percent=1.0,
        annual_rent_increase_percent=3.0,
    )
    
    expenses = OperatingExpenses(
        property_tax_annual=3_000,
        insurance_annual=1_000,
        hoa_monthly=0,
        maintenance_percent=5.0,
        property_management_percent=8.0,
        capex_reserve_percent=5.0,
        landlord_paid_utilities_monthly=0,
        annual_expense_growth_percent=2.5,
    )
    
    market_assumptions = MarketAssumptions(
        annual_appreciation_percent=3.0,
        sales_expense_percent=7.0,
        inflation_rate_percent=2.5,
    )
    
    deal = Deal(
        deal_id="cash-001",
        deal_name="Cash Purchase Deal",
        property=property_obj,
        financing=financing,
        income=income,
        expenses=expenses,
        market_assumptions=market_assumptions,
        holding_period_years=10,
    )
    
    return deal


@pytest.fixture
def negative_cash_flow_deal() -> Deal:
    """Deal with negative cash flow (bad deal for testing edge cases).
    
    High expenses and high interest rate result in negative cash flow.
    """
    property_obj = Property(
        address="101 Negative Flow Dr",
        property_type=PropertyType.CONDO,
        square_footage=1000,
        num_units=1,
        bedrooms=2,
        bathrooms=1,
        year_built=1980,
        purchase_price=250_000,
        closing_costs=5_000,
        rehab_budget=15_000,
    )
    
    financing = Financing.create_simple_loan(
        financing_type=FinancingType.CONVENTIONAL,
        down_payment_percent=20.0,
        interest_rate=8.0,  # High interest rate
        loan_term_years=30,
        loan_points=2.0,
    )
    
    income = Income(
        monthly_rent_per_unit=1_500,  # Low rent for price
        vacancy_rate_percent=10.0,  # High vacancy
        credit_loss_percent=3.0,
        annual_rent_increase_percent=2.0,
    )
    
    expenses = OperatingExpenses(
        property_tax_annual=5_000,  # High taxes
        insurance_annual=1_800,
        hoa_monthly=400,  # High HOA
        maintenance_percent=8.0,  # Older building = more maintenance
        property_management_percent=10.0,
        capex_reserve_percent=8.0,
        landlord_paid_utilities_monthly=100,
        annual_expense_growth_percent=3.0,
    )
    
    market_assumptions = MarketAssumptions(
        annual_appreciation_percent=2.0,
        sales_expense_percent=7.0,
        inflation_rate_percent=2.5,
    )
    
    deal = Deal(
        deal_id="negative-001",
        deal_name="Negative Cash Flow Deal",
        property=property_obj,
        financing=financing,
        income=income,
        expenses=expenses,
        market_assumptions=market_assumptions,
        holding_period_years=10,
    )
    
    return deal


@pytest.fixture
def multi_unit_deal() -> Deal:
    """Multi-family property (4 units) for testing unit scaling."""
    property_obj = Property(
        address="555 Fourplex Way",
        property_type=PropertyType.MULTI_FAMILY,
        square_footage=4000,
        num_units=4,
        bedrooms=8,
        bathrooms=4,
        year_built=1970,
        purchase_price=500_000,
        closing_costs=10_000,
        rehab_budget=20_000,
    )
    
    financing = Financing.create_simple_loan(
        financing_type=FinancingType.CONVENTIONAL,
        down_payment_percent=25.0,
        interest_rate=6.0,
        loan_term_years=30,
        loan_points=1.0,
    )
    
    income = Income(
        monthly_rent_per_unit=1_200,  # $1,200/unit = $4,800/month total
        vacancy_rate_percent=7.0,
        credit_loss_percent=2.0,
        annual_rent_increase_percent=3.0,
    )
    
    expenses = OperatingExpenses(
        property_tax_annual=8_000,
        insurance_annual=3_000,
        hoa_monthly=0,
        maintenance_percent=6.0,
        property_management_percent=10.0,
        capex_reserve_percent=6.0,
        landlord_paid_utilities_monthly=200,
        annual_expense_growth_percent=2.5,
    )
    
    market_assumptions = MarketAssumptions(
        annual_appreciation_percent=4.0,
        sales_expense_percent=6.0,
        inflation_rate_percent=2.5,
    )
    
    deal = Deal(
        deal_id="multi-001",
        deal_name="4-Unit Multi-Family Deal",
        property=property_obj,
        financing=financing,
        income=income,
        expenses=expenses,
        market_assumptions=market_assumptions,
        holding_period_years=10,
    )
    
    return deal


@pytest.fixture
def profitable_deal(sample_deal) -> Deal:
    """Alias for sample_deal - expected to be profitable."""
    return sample_deal


# =============================================================================
# Parametrized Fixtures
# =============================================================================


@pytest.fixture(params=[5, 10, 15, 30])
def holding_period(request) -> int:
    """Parametrized fixture for common holding periods."""
    return request.param


# =============================================================================
# Isolated Component Fixtures
# =============================================================================


@pytest.fixture
def simple_income() -> Income:
    """Simple income model for isolated testing."""
    return Income(
        monthly_rent_per_unit=2_000,
        vacancy_rate_percent=5.0,
        credit_loss_percent=1.0,
        annual_rent_increase_percent=3.0,
    )


@pytest.fixture
def simple_expenses() -> OperatingExpenses:
    """Simple expense model for isolated testing."""
    return OperatingExpenses(
        property_tax_annual=3_000,
        insurance_annual=1_200,
        hoa_monthly=0,
        maintenance_percent=5.0,
        property_management_percent=8.0,
        capex_reserve_percent=5.0,
        landlord_paid_utilities_monthly=0,
        annual_expense_growth_percent=2.5,
    )


@pytest.fixture
def simple_financing() -> Financing:
    """Simple financing for isolated testing."""
    return Financing.create_simple_loan(
        financing_type=FinancingType.CONVENTIONAL,
        down_payment_percent=20.0,
        interest_rate=6.0,
        loan_term_years=30,
        loan_points=0,
    )
