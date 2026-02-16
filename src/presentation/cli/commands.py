"""Command-line interface for Real Estate Investment Analysis."""

import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ...services.deal_service import DealService
from ...adapters.config_loader import ConfigLoader
from ...utils.formatting import format_currency, format_percentage
from ...utils.logging import setup_logging, get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option("--log-level", default="INFO", help="Logging level")
def cli(log_level: str):
    """Real Estate Investment Analysis Tool."""
    setup_logging(log_level=log_level)


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="JSON config file")
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.option("--holding-period", "-h", default=10, help="Holding period in years")
def analyze(
    config: str, output: Optional[str], holding_period: int
):
    """Analyze a real estate deal from config file."""
    logger.info(f"Analyzing deal from config: {config}")

    # Initialize services
    deal_service = DealService()
    config_loader = ConfigLoader()

    # Load configuration
    with open(config, "r") as f:
        config_data = json.load(f)

    # Create deal from config
    deal = deal_service.create_deal_from_config(config_data)

    # Run analysis
    console.print(
        Panel.fit(
            f"[bold blue]Analyzing Deal: {deal.deal_name}[/bold blue]", box=box.DOUBLE
        )
    )

    # Calculate metrics
    try:
        result = deal_service.run_analysis(
            deal,
            holding_period=holding_period,
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    # Display results
    _display_metrics(result.metrics)

    # Save results if requested
    if output:
        _save_results(deal, result.metrics, output)
        console.print(f"[green]Results saved to {output}[/green]")


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="JSON config file")
@click.option("--years", "-y", default=30, help="Years to project")
@click.option("--output", "-o", type=click.Path(), default="output/proforma_output.csv", help="Output CSV file")
def proforma(config: str, years: int, output: Optional[str]):
    """Generate pro-forma projections."""
    logger.info(f"Generating {years}-year pro-forma")

    deal_service = DealService()

    # Load deal
    with open(config, "r") as f:
        config_data = json.load(f)
    deal = deal_service.create_deal_from_config(config_data)

    # Calculate pro-forma
    result = deal_service.calculate_proforma(deal, years=years)

    if not result.success:
        console.print(f"[red]Error: {result.errors}[/red]")
        return

    # Display summary
    df = result.data.to_dataframe()
    _display_proforma_summary(df, years)

    # Save to output directory (create if needed)
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output)
        console.print(f"[green]Pro-forma saved to {output}[/green]")


@cli.command()
@click.option("--loan-amount", "-l", type=float, prompt="Loan amount")
@click.option("--rate", "-r", type=float, prompt="Interest rate (%)")
@click.option("--term", "-t", type=int, default=30, prompt="Loan term (years)")
def amortization(loan_amount: float, rate: float, term: int):
    """Calculate loan amortization schedule."""
    from ...core.models import (
        Property,
        PropertyType,
        Financing,
        FinancingType,
        Income,
        OperatingExpenses,
        Deal,
    )

    # Create minimal deal for calculator
    deal = Deal(
        deal_id="amort-calc",
        deal_name="Amortization Calculator",
        property=Property(
            address="N/A",
            property_type=PropertyType.SINGLE_FAMILY,
            purchase_price=loan_amount / 0.8,
            bedrooms=1,
            bathrooms=1,
        ),
        financing=Financing(
            financing_type=FinancingType.CONVENTIONAL,
            down_payment_percent=20,
            interest_rate=rate,
            loan_term_years=term,
        ),
        income=Income(monthly_rent_per_unit=1000),
        expenses=OperatingExpenses(property_tax_annual=1000, insurance_annual=1000),
    )

    # Calculate
    deal_service = DealService()
    result = deal_service.calculate_amortization(deal)

    if result.success:
        _display_amortization_summary(result.data)


@cli.command()
def list_configs():
    """List available configuration files."""
    config_loader = ConfigLoader()
    configs = config_loader.list_available_configs()

    if configs:
        console.print("[bold]Available Configurations:[/bold]")
        for config_name in configs:
            console.print(f"  - {config_name}")
    else:
        console.print("[yellow]No configuration files found.[/yellow]")


def _display_metrics(metrics):
    """Display metrics in a formatted table."""
    table = Table(title="Key Financial Metrics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Rating", style="yellow")

    for metric in metrics.get_all_metrics():
        rating = (
            metric.performance_rating if metric.performance_rating != "Unknown" else "-"
        )
        metric_name = (
            metric.metric_type.value
            if hasattr(metric.metric_type, "value")
            else metric.metric_type
        )
        table.add_row(
            metric_name.replace("_", " ").title(),
            metric.formatted_value,
            rating,
        )

    console.print(table)


def _display_proforma_summary(df, years):
    """Display pro-forma summary."""
    console.print(
        Panel.fit(f"[bold]{years}-Year Pro-Forma Summary[/bold]", box=box.DOUBLE)
    )

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
                format_currency(row["net_operating_income"]),
                format_currency(row["pre_tax_cash_flow"]),
                format_currency(row["property_value"]),
                format_currency(row["total_equity"]),
            )

    console.print(table)


def _display_amortization_summary(schedule):
    """Display amortization summary."""
    console.print(
        Panel.fit("[bold]Loan Amortization Summary[/bold]", box=box.DOUBLE)
    )

    console.print(f"Loan Amount: {format_currency(schedule.loan_amount)}")
    console.print(f"Interest Rate: {format_percentage(schedule.interest_rate / 100)}")
    console.print(f"Term: {schedule.loan_term_years} years")
    console.print(f"Monthly Payment: {format_currency(schedule.monthly_payment)}")
    console.print(f"Total Interest: {format_currency(schedule.total_interest_paid)}")

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
                    format_currency(row["payment_amount"]),
                    format_currency(row["principal_payment"]),
                    format_currency(row["interest_payment"]),
                    format_currency(row["ending_balance"]),
                )

        console.print(table)


def _save_results(deal, metrics, output_path: str):
    """Save analysis results to file."""
    results = {
        "deal_summary": {
            "name": deal.deal_name,
            "address": deal.property.address,
            "purchase_price": deal.property.purchase_price,
            "total_investment": deal.get_total_cash_needed(),
        },
        "metrics": metrics.to_dict(),
        "year_1": {
            "noi": deal.get_year_1_noi(),
            "cash_flow": deal.get_year_1_cash_flow(),
            "cap_rate": deal.get_cap_rate(),
            "coc_return": deal.get_cash_on_cash_return(),
            "dscr": deal.get_debt_service_coverage_ratio(),
        },
    }

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    cli()
