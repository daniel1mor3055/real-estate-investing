#!/usr/bin/env python3
"""
Real Estate Investment Analysis - Main Demo Script

This demonstrates the modular architecture with proper design patterns.
"""

import json
from pathlib import Path

from src.models import (
    Property, PropertyType, Financing, FinancingType,
    Income, OperatingExpenses, Deal, MarketAssumptions
)
from src.calculators import (
    MetricsCalculator, ProFormaCalculator,
    AmortizationCalculator, CashFlowCalculator
)
from src.utils import setup_logging, get_logger, format_currency, format_percentage

# Setup logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)


def create_sample_deal() -> Deal:
    """Create a sample deal for demonstration."""
    logger.info("Creating sample deal")
    
    # Create property
    property = Property(
        address="123 Oak Street, Denver, CO",
        property_type=PropertyType.SINGLE_FAMILY,
        purchase_price=275000,
        closing_costs=6875,
        rehab_budget=18000,
        num_units=1,
        bedrooms=3,
        bathrooms=2,
        square_footage=1800,
        year_built=1985
    )
    
    # Create financing
    financing = Financing(
        financing_type=FinancingType.CONVENTIONAL,
        is_cash_purchase=False,
        down_payment_percent=20,
        interest_rate=7.25,
        loan_term_years=30,
        loan_points=1.0
    )
    
    # Create income projections
    income = Income(
        monthly_rent_per_unit=2400,
        vacancy_rate_percent=6,
        credit_loss_percent=1,
        annual_rent_increase_percent=2.5
    )
    
    # Add other income sources
    income.add_income_source("parking", 100, "Garage parking")
    income.add_income_source("laundry", 50, "Coin laundry")
    
    # Create expenses
    expenses = OperatingExpenses(
        property_tax_annual=3850,
        insurance_annual=1320,
        hoa_monthly=75,
        maintenance_percent=8,
        property_management_percent=9,
        capex_reserve_percent=5,
        landlord_paid_utilities_monthly=125,
        annual_expense_growth_percent=2.8
    )
    
    # Create market assumptions
    market = MarketAssumptions(
        annual_appreciation_percent=3.2,
        sales_expense_percent=7,
        inflation_rate_percent=2.5
    )
    
    # Create the deal
    deal = Deal(
        deal_id="demo-001",
        deal_name="123 Oak Street Investment",
        property=property,
        financing=financing,
        income=income,
        expenses=expenses,
        market_assumptions=market,
        holding_period_years=10
    )
    
    return deal


def run_analysis(deal: Deal, holding_period: int = 10):
    """Run comprehensive analysis on a deal."""
    print("=" * 80)
    print(f"REAL ESTATE INVESTMENT ANALYSIS: {deal.deal_name}")
    print("=" * 80)
    
    # Display deal summary
    print(f"\nProperty: {deal.property.address}")
    print(f"Purchase Price: {format_currency(deal.property.purchase_price)}")
    print(f"Total Investment: {format_currency(deal.total_cash_needed)}")
    print(f"Financing: {format_currency(deal.financing.loan_amount)} @ {deal.financing.interest_rate}%")
    print("-" * 80)
    
    # Calculate metrics for different investor profiles
    print("\nKEY METRICS BY INVESTOR PROFILE:")
    print("-" * 80)
    
    for profile in ["cash_flow", "balanced", "appreciation"]:
        logger.info(f"Calculating metrics for {profile} investor")
        
        calculator = MetricsCalculator(deal)
        result = calculator.calculate(
            holding_period=holding_period,
            investor_profile=profile
        )
        
        if result.success:
            metrics = result.data
            print(f"\n{profile.upper()} INVESTOR:")
            print(f"  Deal Score: {metrics.deal_score.formatted_value if metrics.deal_score else 'N/A'}")
            print(f"  Year 1 Cap Rate: {metrics.cap_rate.formatted_value}")
            print(f"  Year 1 Cash-on-Cash: {metrics.coc_return.formatted_value}")
            print(f"  {holding_period}-Year IRR: {metrics.irr.formatted_value if metrics.irr else 'N/A'}")
            print(f"  Equity Multiple: {metrics.equity_multiple.formatted_value if metrics.equity_multiple else 'N/A'}")
        else:
            print(f"  Error: {result.errors}")
    
    # Show pro-forma summary
    print("\n" + "=" * 80)
    print(f"{holding_period}-YEAR PRO-FORMA SUMMARY:")
    print("-" * 80)
    
    proforma_calc = ProFormaCalculator(deal)
    proforma_result = proforma_calc.calculate(years=holding_period)
    
    if proforma_result.success:
        df = proforma_result.data.to_dataframe()
        
        # Show key years
        display_years = [1, 5, holding_period]
        print(f"{'Year':<6} {'NOI':>12} {'Cash Flow':>12} {'Property Value':>15} {'Total Equity':>15}")
        print("-" * 65)
        
        for year in display_years:
            if year in df.index:
                row = df.loc[year]
                print(f"{year:<6} "
                      f"{format_currency(row['net_operating_income']):>12} "
                      f"{format_currency(row['pre_tax_cash_flow']):>12} "
                      f"{format_currency(row['property_value']):>15} "
                      f"{format_currency(row['total_equity']):>15}")
    
    # Show amortization summary
    print("\n" + "=" * 80)
    print("LOAN AMORTIZATION SUMMARY:")
    print("-" * 80)
    
    if not deal.financing.is_cash_purchase:
        amort_calc = AmortizationCalculator(deal)
        amort_result = amort_calc.calculate()
        
        if amort_result.success:
            schedule = amort_result.data
            print(f"Loan Amount: {format_currency(schedule.loan_amount)}")
            print(f"Monthly Payment: {format_currency(schedule.monthly_payment)}")
            print(f"Total Interest Paid: {format_currency(schedule.total_interest_paid)}")
            
            # Show first 5 years
            yearly = schedule.get_yearly_summary()
            if len(yearly) > 0:
                print("\nFirst 5 Years Annual Breakdown:")
                print(f"{'Year':<6} {'Payment':>12} {'Principal':>12} {'Interest':>12} {'Balance':>15}")
                print("-" * 60)
                
                for year in range(1, min(6, len(yearly) + 1)):
                    if year in yearly.index:
                        row = yearly.loc[year]
                        print(f"{year:<6} "
                              f"{format_currency(row['payment_amount']):>12} "
                              f"{format_currency(row['principal_payment']):>12} "
                              f"{format_currency(row['interest_payment']):>12} "
                              f"{format_currency(row['ending_balance']):>15}")
    else:
        print("All-cash purchase - no loan amortization")
    
    print("\n" + "=" * 80)
    print("Analysis complete!")


def main():
    """Main entry point."""
    print("REAL ESTATE INVESTMENT ANALYSIS - MODULAR ARCHITECTURE DEMO")
    print("Using Strategy Pattern, Factory Pattern, and Clean Architecture")
    print()
    
    # Option 1: Create deal programmatically
    deal = create_sample_deal()
    
    # Option 2: Load deal from JSON file
    # config_file = Path("sample_deal.json")
    # if config_file.exists():
    #     with open(config_file) as f:
    #         config = json.load(f)
    #     # Create deal from config (implementation would go here)
    
    # Run the analysis
    run_analysis(deal, holding_period=10)
    
    print("\n" + "=" * 80)
    print("ARCHITECTURE HIGHLIGHTS:")
    print("-" * 80)
    print("1. Domain Models: Pydantic-based models with validation (src/models/)")
    print("2. Strategy Pattern: Different investor profiles (src/strategies/)")
    print("3. Calculator Pattern: Modular calculators for each analysis type (src/calculators/)")
    print("4. Clean Architecture: Separation of concerns with distinct layers")
    print("5. Logging: Structured logging with loguru (src/utils/logging.py)")
    print("6. CLI Interface: Rich command-line interface (cli.py)")
    print("7. GUI Interface: Modern Streamlit web app (app.py)")
    print("\nRun 'python cli.py --help' for CLI usage")
    print("Run 'streamlit run app.py' for GUI interface")


if __name__ == "__main__":
    main()