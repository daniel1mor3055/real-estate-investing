"""Quick test to verify ROE implementation matches documentation."""

from src.core.models import Deal, Property, PropertyType, Financing, FinancingType, Income, OperatingExpenses, MarketAssumptions
from src.core.calculators.proforma import ProFormaCalculator
from src.core.calculators.metrics import MetricsCalculator

# Create a test deal matching the documentation example
deal = Deal(
    deal_id="test-roe",
    deal_name="ROE Test Property",
    property=Property(
        address="123 Test St",
        property_type=PropertyType.SINGLE_FAMILY,
        purchase_price=250000,
        bedrooms=3,
        bathrooms=2,
        num_units=1,
    ),
    financing=Financing(
        financing_type=FinancingType.CONVENTIONAL,
        down_payment_percent=20,  # $50,000 down
        interest_rate=4.0,
        loan_term_years=30,
    ),
    income=Income(
        monthly_rent_per_unit=2000,
        other_monthly_income_per_unit=0,
        vacancy_rate_percent=5,
        annual_rent_increase_percent=3,
    ),
    expenses=OperatingExpenses(
        property_tax_annual=3000,
        insurance_annual=1200,
        hoa_monthly=0,
        maintenance_percent=5,
        capex_reserve_percent=5,
        property_management_percent=10,
        annual_expense_growth_percent=3,
    ),
    market_assumptions=MarketAssumptions(
        annual_appreciation_percent=3,
        sales_expense_percent=7,
    ),
    closing_costs=6000,
    initial_rehab_cost=0,
)

print("=" * 80)
print("ROE IMPLEMENTATION TEST")
print("=" * 80)

# Calculate pro-forma
proforma_calc = ProFormaCalculator(deal)
proforma_result = proforma_calc.calculate(years=10)

if proforma_result.success:
    df = proforma_result.data.to_dataframe()
    
    print("\nPro-Forma Year-by-Year ROE:")
    print("-" * 80)
    print(f"{'Year':<6} {'Cash Flow':<15} {'Equity':<15} {'Avg Equity':<15} {'ROE':<10}")
    print("-" * 80)
    
    for year in [0, 1, 2, 3, 5, 10]:
        if year in df.index:
            row = df.loc[year]
            if year == 0:
                print(f"{year:<6} ${row['pre_tax_cash_flow']:>13,.0f} ${row['total_equity']:>13,.0f} {'N/A':<15} {'N/A':<10}")
            else:
                print(f"{year:<6} ${row['pre_tax_cash_flow']:>13,.0f} ${row['total_equity']:>13,.0f} ${row['average_equity']:>13,.0f} {row['roe']:>8.2%}")
    
    print("\n" + "=" * 80)
    
    # Expected values from documentation:
    # Year 1: Cash Flow = $3,953, Equity_0 = $50,000, Equity_1 = $59,598
    # ROE (average) = 3,953 / ((50,000 + 59,598)/2) = 7.21%
    
    year1 = df.loc[1]
    year2 = df.loc[2]
    
    print("\nVERIFICATION AGAINST DOCUMENTATION:")
    print("-" * 80)
    print(f"Year 1 Cash Flow: ${year1['pre_tax_cash_flow']:,.2f}")
    print(f"Year 1 Total Equity: ${year1['total_equity']:,.2f}")
    print(f"Year 1 Average Equity: ${year1['average_equity']:,.2f}")
    print(f"Year 1 ROE: {year1['roe']:.2%}")
    print()
    print(f"Year 2 Cash Flow: ${year2['pre_tax_cash_flow']:,.2f}")
    print(f"Year 2 Total Equity: ${year2['total_equity']:,.2f}")
    print(f"Year 2 Average Equity: ${year2['average_equity']:,.2f}")
    print(f"Year 2 ROE: {year2['roe']:.2%}")
    
    print("\n" + "=" * 80)

# Test metrics calculator
print("\nMETRICS CALCULATOR TEST:")
print("-" * 80)

metrics_calc = MetricsCalculator(deal)
metrics_result = metrics_calc.calculate(holding_period=10, investor_profile="balanced")

if metrics_result.success:
    metrics = metrics_result.data
    
    if metrics.roe_year1:
        print(f"ROE Year 1: {metrics.roe_year1.formatted_value}")
        print(f"  - Performance: {metrics.roe_year1.performance_rating}")
    
    if metrics.average_roe:
        print(f"Average ROE (10 years): {metrics.average_roe.formatted_value}")
        print(f"  - Performance: {metrics.average_roe.performance_rating}")
    
    print("\nAll Metrics:")
    for metric in metrics.get_all_metrics():
        if metric:
            print(f"  {metric.metric_type}: {metric.formatted_value}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
