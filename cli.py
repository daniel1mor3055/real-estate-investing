#!/usr/bin/env python3
"""Command-line interface for Real Estate Investment Analysis.

This is a thin wrapper that imports and runs the CLI from the presentation layer.

Usage:
    python cli.py --help
    python cli.py analyze -c sample_deal.json
    python cli.py proforma -c sample_deal.json -y 10
    python cli.py amortization -l 200000 -r 7 -t 30
"""

from src.presentation.cli.commands import cli

if __name__ == "__main__":
    cli()
