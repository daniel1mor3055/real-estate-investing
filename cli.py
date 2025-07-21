#!/usr/bin/env python3
"""Command-line interface for Real Estate Investment Analysis."""

import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.models import (
    Property, PropertyType, Financing, FinancingType,
    Income, OperatingExpenses, Deal, MarketAssumptions
)
from src.calculators import (
    MetricsCalculator, ProFormaCalculator,
    AmortizationCalculator, CashFlowCalculator
)
from src.utils import setup_logging, get_logger, format_currency, format_percentage

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option('--log-level', default='INFO', help='Logging level')
def cli(log_level: str):
    """Real Estate Investment Analysis Tool."""
    setup_logging(log_level=log_level)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='JSON config file')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--holding-period', '-h', default=10, help='Holding period in years')
@click.option('--investor-profile', '-p', 
              type=click.Choice(['cash_flow', 'balanced', 'appreciation']),
              default='balanced', help='Investor profile')
def analyze(config: str, output: Optional[str], holding_period: int, investor_profile: str):
    """Analyze a real estate deal from config file."""
    logger.info(f"Analyzing deal from config: {config}")
    
    # Load configuration
    with open(config, 'r') as f:
        config_data = json.load(f)
    
    # Create deal from config
    deal = create_deal_from_config(config_data)
    
    # Run analysis
    console.print(Panel.fit(
        f"[bold blue]Analyzing Deal: {deal.deal_name}[/bold blue]",
        box=box.DOUBLE
    ))
    
    # Calculate metrics
    metrics_calc = MetricsCalculator(deal)
    metrics_result = metrics_calc.calculate(
        holding_period=holding_period,
        investor_profile=investor_profile
    )
    
    if not metrics_result.success:
        console.print(f"[red]Error calculating metrics: {metrics_result.errors}[/red]")
        return
    
    # Display results
    display_metrics(metrics_result.data)
    
    # Save results if requested
    if output:
        save_results(deal, metrics_result.data, output)
        console.print(f"[green]Results saved to {output}[/green]")


@cli.command()
@click.option('--address', prompt='Property address', help='Property address')
@click.option('--price', prompt='Purchase price', type=float, help='Purchase price')
@click.option('--rent', prompt='Monthly rent', type=float, help='Monthly rent per unit')
@click.option('--units', default=1, help='Number of units')
def quick(address: str, price: float, rent: float, units: int):
    """Quick analysis with minimal inputs."""
    logger.info("Running quick analysis")
    
    # Create deal with defaults
    deal = Deal(
        deal_id="quick-analysis",
        deal_name=f"Quick Analysis - {address}",
        property=Property(
            address=address,
            property_type=PropertyType.SINGLE_FAMILY,
            purchase_price=price,
            closing_costs=price * 0.025,  # 2.5% default
            rehab_budget=0,
            num_units=units,
            bedrooms=3,  # Default
            bathrooms=2  # Default
        ),
        financing=Financing(
            financing_type=FinancingType.CONVENTIONAL,
            down_payment_percent=20,
            interest_rate=7.0,
            loan_term_years=30
        ),
        income=Income(
            monthly_rent_per_unit=rent,
            vacancy_rate_percent=5,
            annual_rent_increase_percent=3
        ),
        expenses=OperatingExpenses(
            property_tax_annual=price * 0.012,  # 1.2% default
            insurance_annual=price * 0.004,  # 0.4% default
            maintenance_percent=5,
            property_management_percent=8,
            capex_reserve_percent=5
        )
    )
    
    # Calculate and display
    display_quick_analysis(deal)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='JSON config file')
@click.option('--years', '-y', default=30, help='Years to project')
@click.option('--output', '-o', type=click.Path(), help='Output CSV file')
def proforma(config: str, years: int, output: Optional[str]):
    """Generate pro-forma projections."""
    logger.info(f"Generating {years}-year pro-forma")
    
    # Load deal
    with open(config, 'r') as f:
        config_data = json.load(f)
    deal = create_deal_from_config(config_data)
    
    # Calculate pro-forma
    calc = ProFormaCalculator(deal)
    result = calc.calculate(years=years)
    
    if not result.success:
        console.print(f"[red]Error: {result.errors}[/red]")
        return
    
    # Display summary
    df = result.data.to_dataframe()
    display_proforma_summary(df, years)
    
    # Save if requested
    if output:
        df.to_csv(output)
        console.print(f"[green]Pro-forma saved to {output}[/green]")


@cli.command()
@click.option('--loan-amount', '-l', type=float, prompt='Loan amount')
@click.option('--rate', '-r', type=float, prompt='Interest rate (%)')
@click.option('--term', '-t', type=int, default=30, prompt='Loan term (years)')
def amortization(loan_amount: float, rate: float, term: int):
    """Calculate loan amortization schedule."""
    # Create minimal deal for calculator
    deal = Deal(
        deal_id="amort-calc",
        deal_name="Amortization Calculator",
        property=Property(
            address="N/A",
            property_type=PropertyType.SINGLE_FAMILY,
            purchase_price=loan_amount / 0.8,  # Assume 20% down
            bedrooms=1,
            bathrooms=1
        ),
        financing=Financing(
            financing_type=FinancingType.CONVENTIONAL,
            down_payment_percent=20,
            interest_rate=rate,
            loan_term_years=term
        ),
        income=Income(monthly_rent_per_unit=1000),  # Dummy
        expenses=OperatingExpenses(
            property_tax_annual=1000,  # Dummy
            insurance_annual=1000  # Dummy
        )
    )
    
    # Calculate
    calc = AmortizationCalculator(deal)
    result = calc.calculate()
    
    if result.success:
        display_amortization_summary(result.data)


def create_deal_from_config(config: dict) -> Deal:
    """Create Deal object from configuration dictionary."""
    # Property
    prop_config = config['property']
    property = Property(
        address=prop_config['address'],
        property_type=PropertyType(prop_config.get('type', 'single_family')),
        purchase_price=prop_config['purchase_price'],
        closing_costs=prop_config.get('closing_costs', 0),
        rehab_budget=prop_config.get('rehab_budget', 0),
        num_units=prop_config.get('units', 1),
        bedrooms=prop_config.get('bedrooms', 3),
        bathrooms=prop_config.get('bathrooms', 2),
        square_footage=prop_config.get('square_footage'),
        year_built=prop_config.get('year_built')
    )
    
    # Financing
    fin_config = config['financing']
    financing = Financing(
        financing_type=FinancingType(fin_config.get('type', 'conventional')),
        is_cash_purchase=fin_config.get('cash_purchase', False),
        down_payment_percent=fin_config.get('down_payment_percent', 20),
        interest_rate=fin_config.get('interest_rate', 7),
        loan_term_years=fin_config.get('loan_term', 30),
        loan_points=fin_config.get('points', 0)
    )
    
    # Income
    inc_config = config['income']
    income = Income(
        monthly_rent_per_unit=inc_config['monthly_rent'],
        vacancy_rate_percent=inc_config.get('vacancy_rate', 5),
        credit_loss_percent=inc_config.get('credit_loss', 1),
        annual_rent_increase_percent=inc_config.get('annual_increase', 3)
    )
    
    # Add other income sources if provided
    if 'other_income' in inc_config:
        for item in inc_config['other_income']:
            income.add_income_source(
                source=item['type'],
                monthly_amount=item['amount'],
                description=item.get('description'),
                is_per_unit=item.get('per_unit', False)
            )
    
    # Expenses
    exp_config = config['expenses']
    expenses = OperatingExpenses(
        property_tax_annual=exp_config['property_tax'],
        insurance_annual=exp_config['insurance'],
        hoa_monthly=exp_config.get('hoa', 0),
        maintenance_percent=exp_config.get('maintenance_percent', 5),
        property_management_percent=exp_config.get('management_percent', 8),
        capex_reserve_percent=exp_config.get('capex_percent', 5),
        landlord_paid_utilities_monthly=exp_config.get('utilities', 0),
        annual_expense_growth_percent=exp_config.get('annual_increase', 3)
    )
    
    # Market assumptions
    market_config = config.get('market', {})
    market = MarketAssumptions(
        annual_appreciation_percent=market_config.get('appreciation', 3.5),
        sales_expense_percent=market_config.get('sales_expense', 7),
        inflation_rate_percent=market_config.get('inflation', 2.5)
    )
    
    # Create deal
    deal = Deal(
        deal_id=config.get('id', 'deal-001'),
        deal_name=config.get('name', property.address),
        property=property,
        financing=financing,
        income=income,
        expenses=expenses,
        market_assumptions=market,
        holding_period_years=config.get('holding_period', 10)
    )
    
    return deal


def display_metrics(metrics):
    """Display metrics in a formatted table."""
    # Basic metrics table
    table = Table(title="Key Financial Metrics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Rating", style="yellow")
    
    # Add rows
    for metric in metrics.get_all_metrics():
        rating = metric.performance_rating if metric.performance_rating != "Unknown" else "-"
        table.add_row(
            metric.metric_type.value.replace('_', ' ').title(),
            metric.formatted_value,
            rating
        )
    
    console.print(table)


def display_quick_analysis(deal: Deal):
    """Display quick analysis results."""
    console.print(Panel.fit(
        f"[bold]Quick Analysis: {deal.property.address}[/bold]",
        box=box.DOUBLE
    ))
    
    # Key numbers
    console.print(f"Purchase Price: {format_currency(deal.property.purchase_price)}")
    console.print(f"Total Investment: {format_currency(deal.total_cash_needed)}")
    console.print(f"Monthly Rent: {format_currency(deal.income.monthly_rent_per_unit * deal.property.num_units)}")
    console.print()
    
    # Year 1 metrics
    console.print("[bold]Year 1 Projections:[/bold]")
    console.print(f"  NOI: {format_currency(deal.year_1_noi)}")
    console.print(f"  Cash Flow: {format_currency(deal.year_1_cash_flow)}")
    console.print(f"  Cap Rate: {format_percentage(deal.cap_rate)}")
    console.print(f"  Cash-on-Cash: {format_percentage(deal.cash_on_cash_return)}")
    console.print(f"  DSCR: {deal.debt_service_coverage_ratio:.2f}x")


def display_proforma_summary(df, years):
    """Display pro-forma summary."""
    console.print(Panel.fit(
        f"[bold]{years}-Year Pro-Forma Summary[/bold]",
        box=box.DOUBLE
    ))
    
    # Show years 1, 5, 10, and final
    display_years = [1, 5, 10, years] if years >= 10 else [1, years]
    display_years = [y for y in display_years if y <= years]
    
    table = Table(box=box.ROUNDED)
    table.add_column("Year", style="cyan")
    table.add_column("NOI", style="green")
    table.add_column("Cash Flow", style="green")
    table.add_column("Property Value", style="blue")
    table.add_column("Equity", style="yellow")
    
    for year in display_years:
        if year in df.index:
            row = df.loc[year]
            table.add_row(
                str(year),
                format_currency(row['net_operating_income']),
                format_currency(row['pre_tax_cash_flow']),
                format_currency(row['property_value']),
                format_currency(row['total_equity'])
            )
    
    console.print(table)


def display_amortization_summary(schedule):
    """Display amortization summary."""
    console.print(Panel.fit(
        "[bold]Loan Amortization Summary[/bold]",
        box=box.DOUBLE
    ))
    
    console.print(f"Loan Amount: {format_currency(schedule.loan_amount)}")
    console.print(f"Interest Rate: {format_percentage(schedule.interest_rate/100)}")
    console.print(f"Term: {schedule.loan_term_years} years")
    console.print(f"Monthly Payment: {format_currency(schedule.monthly_payment)}")
    console.print(f"Total Interest: {format_currency(schedule.total_interest_paid)}")
    
    # Show yearly summary for first 5 years
    yearly = schedule.get_yearly_summary()
    if len(yearly) > 0:
        console.print("\n[bold]First 5 Years:[/bold]")
        table = Table(box=box.SIMPLE)
        table.add_column("Year")
        table.add_column("Payment")
        table.add_column("Principal")
        table.add_column("Interest")
        table.add_column("Balance")
        
        for year in range(1, min(6, len(yearly) + 1)):
            if year in yearly.index:
                row = yearly.loc[year]
                table.add_row(
                    str(year),
                    format_currency(row['payment_amount']),
                    format_currency(row['principal_payment']),
                    format_currency(row['interest_payment']),
                    format_currency(row['ending_balance'])
                )
        
        console.print(table)


def save_results(deal: Deal, metrics, output_path: str):
    """Save analysis results to file."""
    results = {
        'deal_summary': {
            'name': deal.deal_name,
            'address': deal.property.address,
            'purchase_price': deal.property.purchase_price,
            'total_investment': deal.total_cash_needed
        },
        'metrics': metrics.to_dict(),
        'year_1': {
            'noi': deal.year_1_noi,
            'cash_flow': deal.year_1_cash_flow,
            'cap_rate': deal.cap_rate,
            'coc_return': deal.cash_on_cash_return,
            'dscr': deal.debt_service_coverage_ratio
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


if __name__ == '__main__':
    cli() 