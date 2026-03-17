# AGENTS.md

## Project Overview

Rental property investment analysis tool focused on the Israeli real estate market. Supports deal modeling, financial metrics, multi-year pro-forma projections, and Israeli multi-track mortgage amortization (מסלולים). Provides both a Streamlit web UI and a Click-based CLI.

## Architecture

Layered architecture with strict dependency direction: **core → services → adapters → presentation**.

```
src/
├── core/           # Domain models (Pydantic v2) and calculators
│   ├── models/     # Deal, Property, Financing, Income, Expenses, Metrics
│   └── calculators/# Amortization, CashFlow, Metrics, ProForma (all extend base Calculator)
├── services/       # Orchestration: DealService, AnalysisService
├── adapters/       # I/O: ConfigLoader (JSON), DealRepository
├── analysis/       # Sensitivity and scenario analysis
├── presentation/   # CLI (Click + Rich) and Streamlit UI
├── utils/          # Formatting, logging, metrics info
└── config/         # metrics_definitions.json
```

Entry points:
- `app.py` — Streamlit GUI (`streamlit run app.py`)
- `cli.py` — CLI (`venv/bin/python3 cli.py --help`)
- `scripts/` — Standalone analysis scripts

## Tech Stack

| Layer | Libraries |
|-------|-----------|
| Models | Pydantic v2 |
| Numerics | pandas, numpy, numpy-financial |
| Visualization | matplotlib, seaborn, plotly |
| Web UI | Streamlit |
| CLI | Click, Rich |
| Logging | Loguru |

Dependencies are in `requirements.txt` (no pyproject.toml).

## Python Environment

- Always use the local venv: `venv/bin/python3`, `venv/bin/pip3`
- Never use `source activate` or global `python`/`pip`
- Create venv if missing: `[ ! -d "venv" ] && python3 -m venv venv`

## Domain Concepts

**Israeli Mortgage Tracks**: A single mortgage is composed of multiple parallel sub-loans (tracks), each with its own type, rate, term, and repayment method.

Track types: `fixed_unlinked` (קל"צ), `fixed_cpi_linked`, `prime`, `variable_1y`/`2y`/`5y`/`10y`

Repayment methods: `spitzer` (annuity), `equal_principal`, `bullet`

Each track supports grace periods, mid-term rate changes, prepayments, and CPI indexation.

**Key Metrics**: NOI, Cap Rate, Cash-on-Cash Return, DSCR, IRR, Equity Multiple, ROE, NPV

**Deal Configs**: JSON files in `deals/` define a full deal (property, financing, income, expenses, market assumptions, holding period).

## Code Patterns

- **Calculators** inherit from `Calculator` base class and return `CalculatorResult[T]`
- **Models** are Pydantic v2 `BaseModel` with validation
- **Services** orchestrate calculators and adapters — keep business logic in services, not in presentation
- **Adapters** handle persistence (JSON files, in-memory) behind abstract repository interfaces
- Monetary values are in the deal's native currency (typically ILS)

## Adding a New Calculator

1. Create class in `src/core/calculators/` extending `Calculator`
2. Return results via `CalculatorResult[T]`
3. Wire through `DealService` or `AnalysisService`
4. Expose via CLI command and/or Streamlit page

## Adding a New Deal Model Field

1. Update the relevant Pydantic model in `src/core/models/`
2. Update `src/adapters/config_loader.py` if JSON schema changes
3. Update calculators that consume the field
4. Update UI components if user-facing

## Reference Documentation

- `docs/CONTEXT.md` — Quantitative framework: all formulas, metrics definitions, and financial theory
- `docs/roe/CONTEXT_with_ROE.md` — ROE analysis context
- `docs/tooltips/tooltips.md` — UI tooltip text
- `src/config/metrics_definitions.json` — Metric metadata, formulas, benchmarks
