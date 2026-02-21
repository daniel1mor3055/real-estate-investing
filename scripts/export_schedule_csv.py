#!/usr/bin/env python3
"""
Export the full amortization schedule to CSV (one file per track).
Useful for comparing against Mashkantaman or any reference calculator.

Usage:
    venv/bin/python3 scripts/export_schedule_csv.py deals/test_deals/01_spitzer_baseline.json
    venv/bin/python3 scripts/export_schedule_csv.py deals/itzhak_navon_21.json --output-dir /tmp/schedules
    venv/bin/python3 scripts/export_schedule_csv.py deals/test_deals/05_two_tracks_spitzer_equal.json --combined
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console

from src.services.deal_service import DealService
from src.core.calculators.amortization import AmortizationCalculator

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export amortization schedule(s) to CSV for external comparison.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export each track to its own CSV (default: output/<deal_name>/<track>.csv)
  venv/bin/python3 scripts/export_schedule_csv.py deals/test_deals/01_spitzer_baseline.json

  # Custom output directory
  venv/bin/python3 scripts/export_schedule_csv.py deals/test_deals/08_rate_change.json --output-dir /tmp/compare

  # Also write a combined CSV summing all tracks per month
  venv/bin/python3 scripts/export_schedule_csv.py deals/test_deals/10_full_complexity.json --combined

  # Specific track only
  venv/bin/python3 scripts/export_schedule_csv.py deals/test_deals/05_two_tracks_spitzer_equal.json --track "Track A"
        """,
    )
    parser.add_argument("deal", help="Path to deal JSON file")
    parser.add_argument(
        "--output-dir", "-o",
        metavar="DIR",
        default=None,
        help="Directory to write CSV files (default: output/<deal_stem>/)",
    )
    parser.add_argument(
        "--combined", "-c",
        action="store_true",
        help="Also write a combined CSV summing all tracks per month.",
    )
    parser.add_argument(
        "--track", "-t",
        metavar="NAME",
        default=None,
        help="Export only this track (partial match, case-insensitive).",
    )
    return parser.parse_args()


COLUMNS = ["Month", "Year", "Payment", "Interest", "Principal", "Balance", "Events"]


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def schedule_to_rows(sched):
    return [
        {
            "Month": p.payment_number,
            "Year": p.year,
            "Payment": round(p.payment_amount, 2),
            "Interest": round(p.interest_payment, 2),
            "Principal": round(p.principal_payment, 2),
            "Balance": round(p.ending_balance, 2),
            "Events": " | ".join(p.events) if p.events else "",
        }
        for p in sched
    ]


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

    # Determine output directory
    out_dir = Path(args.output_dir) if args.output_dir else Path("output") / deal_path.stem

    deal_name = cfg.get("name", deal_path.stem)
    console.print(f"\n[bold]{deal_name}[/bold]  [dim]{deal_path}[/dim]")

    all_schedules = {}

    for sl in deal.financing.sub_loans:
        if args.track and args.track.lower() not in sl.name.lower():
            continue

        sched = AmortizationCalculator.generate_track_schedule(sl)
        rows = schedule_to_rows(sched)
        all_schedules[sl.name] = rows

        safe_name = sl.name.replace(" ", "_").replace("/", "-")
        csv_path = out_dir / f"{safe_name}.csv"
        written = write_csv(csv_path, rows)

        total_p = sum(r["Principal"] for r in rows)
        total_i = sum(r["Interest"]  for r in rows)
        event_months = [r["Month"] for r in rows if r["Events"]]

        console.print(
            f"  [green]✓[/green] [cyan]{sl.name}[/cyan]  →  {written}\n"
            f"    [dim]{len(rows)} months | "
            f"Principal: {total_p:,.2f} | Interest: {total_i:,.2f}"
            + (f" | Events at months: {event_months}" if event_months else "")
            + "[/dim]"
        )

    # Combined CSV
    if args.combined and len(all_schedules) > 1:
        max_month = max(r["Month"] for rows in all_schedules.values() for r in rows)
        combined_rows = []
        for m in range(1, max_month + 1):
            total = {"Month": m, "Year": (m - 1) // 12 + 1,
                     "Payment": 0.0, "Interest": 0.0, "Principal": 0.0,
                     "Balance": 0.0, "Events": ""}
            events = []
            for track_name, rows in all_schedules.items():
                row_map = {r["Month"]: r for r in rows}
                if m in row_map:
                    r = row_map[m]
                    total["Payment"]   += r["Payment"]
                    total["Interest"]  += r["Interest"]
                    total["Principal"] += r["Principal"]
                    total["Balance"]   += r["Balance"]
                    if r["Events"]:
                        events.append(f"{track_name}: {r['Events']}")

            total["Payment"]   = round(total["Payment"],   2)
            total["Interest"]  = round(total["Interest"],  2)
            total["Principal"] = round(total["Principal"], 2)
            total["Balance"]   = round(total["Balance"],   2)
            total["Events"]    = " | ".join(events)
            combined_rows.append(total)

        combined_path = out_dir / "combined.csv"
        write_csv(combined_path, combined_rows)
        total_p = sum(r["Principal"] for r in combined_rows)
        total_i = sum(r["Interest"]  for r in combined_rows)
        console.print(
            f"  [green]✓[/green] [bold]Combined[/bold]  →  {combined_path}\n"
            f"    [dim]Total principal: {total_p:,.2f} | Total interest: {total_i:,.2f}[/dim]"
        )

    console.print(f"\n[bold green]Done.[/bold green] Files written to [cyan]{out_dir}/[/cyan]")


if __name__ == "__main__":
    main()
