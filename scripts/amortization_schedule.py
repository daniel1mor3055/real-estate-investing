#!/usr/bin/env python3
"""
Print a month-by-month amortization schedule for every track in a deal.

Usage:
    venv/bin/python3 scripts/amortization_schedule.py deals/test_deals/01_spitzer_baseline.json
    venv/bin/python3 scripts/amortization_schedule.py deals/test_deals/08_rate_change.json --months 1-65
    venv/bin/python3 scripts/amortization_schedule.py deals/itzhak_navon_21.json --events-only
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.services.deal_service import DealService
from src.core.calculators.amortization import AmortizationCalculator

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Print month-by-month amortization schedule for a deal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # All months, all tracks
  venv/bin/python3 scripts/amortization_schedule.py deals/test_deals/01_spitzer_baseline.json

  # Only months 55-70 (around an event)
  venv/bin/python3 scripts/amortization_schedule.py deals/test_deals/08_rate_change.json --months 55-70

  # Only rows where something happens (rate change, grace end, prepayment)
  venv/bin/python3 scripts/amortization_schedule.py deals/test_deals/10_full_complexity.json --events-only

  # Specific track by name
  venv/bin/python3 scripts/amortization_schedule.py deals/test_deals/05_two_tracks_spitzer_equal.json --track "Track A"
        """,
    )
    parser.add_argument("deal", help="Path to deal JSON file")
    parser.add_argument(
        "--months", "-m",
        metavar="START-END",
        default=None,
        help="Month range to display, e.g. '1-24' or '58-65'. Default: all months.",
    )
    parser.add_argument(
        "--events-only", "-e",
        action="store_true",
        help="Only print months where an event occurs (grace end, rate change, prepayment).",
    )
    parser.add_argument(
        "--track", "-t",
        metavar="NAME",
        default=None,
        help="Filter to a specific track by name (partial match, case-insensitive).",
    )
    return parser.parse_args()


def parse_month_range(months_str: str):
    """Parse '1-24' → (1, 24)."""
    parts = months_str.split("-")
    if len(parts) == 2:
        return int(parts[0]), int(parts[1])
    if len(parts) == 1:
        m = int(parts[0])
        return m, m
    raise ValueError(f"Invalid month range: {months_str}")


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

    if not deal.financing.sub_loans:
        console.print("[red]No Israeli mortgage tracks found in this deal.[/red]")
        sys.exit(1)

    month_start, month_end = None, None
    if args.months:
        month_start, month_end = parse_month_range(args.months)

    console.print(Panel.fit(
        f"[bold blue]{cfg.get('name', deal_path.stem)}[/bold blue]\n"
        f"[dim]{deal_path}[/dim]",
        box=box.DOUBLE,
    ))

    def make_schedule_table(title: str, sched, title_style: str = "bold cyan") -> tuple:
        """Build a Rich table from a schedule. Returns (table, rows_shown, total_p, total_i)."""
        sl_table = Table(box=box.SIMPLE_HEAVY, show_header=True)
        sl_table.add_column("Month", style="cyan", justify="right")
        sl_table.add_column("Payment", justify="right")
        sl_table.add_column("Interest", justify="right", style="yellow")
        sl_table.add_column("Principal", justify="right", style="green")
        sl_table.add_column("Balance", justify="right")
        sl_table.add_column("Events", style="magenta")

        rows_shown = 0
        for p in sched:
            m = p.payment_number
            if month_start is not None and not (month_start <= m <= month_end):
                continue
            if args.events_only and not p.events:
                continue
            sl_table.add_row(
                str(m),
                f"{p.payment_amount:,.2f}",
                f"{p.interest_payment:,.2f}",
                f"{p.principal_payment:,.2f}",
                f"{p.ending_balance:,.2f}",
                "  ".join(p.events) if p.events else "",
            )
            rows_shown += 1

        total_p = sum(p.principal_payment for p in sched)
        total_i = sum(p.interest_payment for p in sched)
        return sl_table, rows_shown, total_p, total_i

    # --- Collect all schedules (respecting --track filter) ---
    all_schedules: dict[str, list] = {}

    for sl in deal.financing.sub_loans:
        if args.track and args.track.lower() not in sl.name.lower():
            continue

        sched = AmortizationCalculator.generate_track_schedule(sl)
        all_schedules[sl.name] = sched

        sl.calculate_effective_rate()
        grace_str = (
            f"  Grace: {sl.grace_period.duration_months}m {sl.grace_period.grace_type.value}"
            if sl.grace_period else ""
        )
        rc_str = (
            f"  Rate changes: {', '.join(f'm{rc.month} {rc.delta:+.1f}%' for rc in sl.rate_changes)}"
            if sl.rate_changes else ""
        )
        pp_str = (
            f"  Prepayments: {', '.join(f'm{pp.month} {pp.amount:,.0f} ({pp.option.value})' for pp in sl.prepayments)}"
            if sl.prepayments else ""
        )

        console.print(
            f"\n[bold cyan]{sl.name}[/bold cyan]  "
            f"[dim]{sl.track_type.value} | {sl.effective_interest_rate:.2f}% | "
            f"{sl.loan_amount:,.0f} | {sl.loan_term_months}m | {sl.repayment_method.value}"
            f"{grace_str}{rc_str}{pp_str}[/dim]"
        )

        tbl, rows_shown, total_p, total_i = make_schedule_table(sl.name, sched)
        console.print(tbl)
        console.print(
            f"  [dim]Total months: {len(sched)} | "
            f"Principal repaid: {total_p:,.2f} | "
            f"Total interest: {total_i:,.2f}[/dim]"
        )
        if rows_shown == 0:
            console.print("  [yellow](No rows match the filter)[/yellow]")

    # --- Combined summary table (only when there are multiple tracks) ---
    if len(all_schedules) > 1:
        max_month = max(p.payment_number for sched in all_schedules.values() for p in sched)
        track_maps = {
            name: {p.payment_number: p for p in sched}
            for name, sched in all_schedules.items()
        }

        combined: list[dict] = []
        for m in range(1, max_month + 1):
            total_pay = total_int = total_pri = total_bal = 0.0
            events: list[str] = []
            for track_name, pmap in track_maps.items():
                p = pmap.get(m)
                if p:
                    total_pay += p.payment_amount
                    total_int += p.interest_payment
                    total_pri += p.principal_payment
                    total_bal += p.ending_balance
                    for e in p.events:
                        events.append(f"{track_name}: {e}")
            if total_pay > 0 or total_bal > 0:
                combined.append({
                    "month": m,
                    "payment": round(total_pay, 2),
                    "interest": round(total_int, 2),
                    "principal": round(total_pri, 2),
                    "balance": round(total_bal, 2),
                    "events": events,
                })

        console.print(f"\n[bold white on blue] COMBINED – All Tracks [/bold white on blue]")

        comb_table = Table(box=box.SIMPLE_HEAVY, show_header=True)
        comb_table.add_column("Month", style="cyan", justify="right")
        comb_table.add_column("Payment", justify="right")
        comb_table.add_column("Interest", justify="right", style="yellow")
        comb_table.add_column("Principal", justify="right", style="green")
        comb_table.add_column("Balance", justify="right")
        comb_table.add_column("Events", style="magenta")

        rows_shown = 0
        for row in combined:
            m = row["month"]
            if month_start is not None and not (month_start <= m <= month_end):
                continue
            if args.events_only and not row["events"]:
                continue
            comb_table.add_row(
                str(m),
                f"{row['payment']:,.2f}",
                f"{row['interest']:,.2f}",
                f"{row['principal']:,.2f}",
                f"{row['balance']:,.2f}",
                "  ".join(row["events"]) if row["events"] else "",
            )
            rows_shown += 1

        console.print(comb_table)

        grand_p = sum(r["principal"] for r in combined)
        grand_i = sum(r["interest"]  for r in combined)
        console.print(
            f"  [dim]Total months: {max_month} | "
            f"Total principal: {grand_p:,.2f} | "
            f"Total interest: {grand_i:,.2f}[/dim]"
        )
        if rows_shown == 0:
            console.print("  [yellow](No rows match the filter)[/yellow]")


if __name__ == "__main__":
    main()
