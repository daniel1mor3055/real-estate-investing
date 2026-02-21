#!/usr/bin/env python3
"""
Run full deal analysis (financial metrics + pro-forma summary).

Usage:
    venv/bin/python3 scripts/analyze_deal.py deals/test_deals/01_spitzer_baseline.json
    venv/bin/python3 scripts/analyze_deal.py deals/itzhak_navon_21.json --holding-period 15
"""

import argparse
import json
import sys
from pathlib import Path

# Make sure the project root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.services.deal_service import DealService

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run full analysis on a deal JSON file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  venv/bin/python3 scripts/analyze_deal.py deals/test_deals/01_spitzer_baseline.json
  venv/bin/python3 scripts/analyze_deal.py deals/itzhak_navon_21.json --holding-period 15
  venv/bin/python3 scripts/analyze_deal.py deals/test_deals/10_full_complexity.json -hp 20
        """,
    )
    parser.add_argument("deal", help="Path to deal JSON file")
    parser.add_argument(
        "--holding-period", "-hp",
        type=int,
        default=10,
        metavar="YEARS",
        help="Holding period in years (default: 10)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    deal_path = Path(args.deal)

    if not deal_path.exists():
        console.print(f"[red]File not found: {deal_path}[/red]")
        sys.exit(1)

    with open(deal_path) as f:
        cfg = json.load(f)

    ds = DealService()
    deal = ds.create_deal_from_config(cfg)
    deal.financing.calculate_loan_details(deal.property.purchase_price)

    console.print(Panel.fit(
        f"[bold blue]{deal.deal_name}[/bold blue]\n"
        f"[dim]{deal_path}[/dim]",
        box=box.DOUBLE,
    ))

    # --- Financing summary ---
    console.print("\n[bold cyan]Financing[/bold cyan]")
    fin_table = Table(box=box.SIMPLE_HEAVY, show_header=True)
    fin_table.add_column("Track", style="cyan")
    fin_table.add_column("Type")
    fin_table.add_column("Amount", justify="right")
    fin_table.add_column("Rate", justify="right")
    fin_table.add_column("Term", justify="right")
    fin_table.add_column("Method")
    fin_table.add_column("Grace")
    fin_table.add_column("Events")

    for sl in deal.financing.sub_loans:
        sl.calculate_effective_rate()
        grace_str = (
            f"{sl.grace_period.duration_months}m {sl.grace_period.grace_type.value}"
            if sl.grace_period else "–"
        )
        events = []
        if sl.rate_changes:
            events.append(f"{len(sl.rate_changes)} rate change(s)")
        if sl.prepayments:
            events.append(f"{len(sl.prepayments)} prepayment(s)")
        fin_table.add_row(
            sl.name,
            sl.track_type.value,
            f"{sl.loan_amount:,.0f}",
            f"{sl.effective_interest_rate:.2f}%",
            f"{sl.loan_term_months}m",
            sl.repayment_method.value,
            grace_str,
            ", ".join(events) if events else "–",
        )
    console.print(fin_table)

    # --- Key metrics ---
    console.print("\n[bold cyan]Key Metrics[/bold cyan]")
    try:
        result = ds.run_analysis(deal, holding_period=args.holding_period)
        metrics_table = Table(box=box.SIMPLE_HEAVY)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green", justify="right")
        metrics_table.add_column("Rating", style="yellow")
        for m in result.metrics.get_all_metrics():
            name = m.metric_type.value if hasattr(m.metric_type, "value") else m.metric_type
            rating = m.performance_rating if m.performance_rating != "Unknown" else "–"
            metrics_table.add_row(name.replace("_", " ").title(), m.formatted_value, rating)
        console.print(metrics_table)

        # --- Pro-forma snapshot ---
        if result.proforma:
            console.print(f"\n[bold cyan]Pro-Forma Snapshot ({args.holding_period}yr)[/bold cyan]")
            df = result.proforma.to_dataframe()
            pf_table = Table(box=box.SIMPLE_HEAVY)
            pf_table.add_column("Year", style="cyan", justify="right")
            pf_table.add_column("NOI", justify="right")
            pf_table.add_column("Cash Flow", justify="right")
            pf_table.add_column("Property Value", justify="right")
            pf_table.add_column("Equity", justify="right")
            snap_years = sorted({1, args.holding_period // 2, args.holding_period} & set(df.index))
            for yr in snap_years:
                row = df.loc[yr]
                pf_table.add_row(
                    str(yr),
                    f"{row['net_operating_income']:,.0f}",
                    f"{row['pre_tax_cash_flow']:,.0f}",
                    f"{row['property_value']:,.0f}",
                    f"{row['total_equity']:,.0f}",
                )
            console.print(pf_table)

    except Exception as e:
        console.print(f"[yellow]Analysis skipped (financing-only deal?): {e}[/yellow]")


if __name__ == "__main__":
    main()
