# Real Estate Investment Analyzer — Product Context

> This document is written for an AI agent tasked with preparing the product owner for a sales meeting with **mortgage advisors and real estate investors**. It provides a complete picture of what the product does, who it is for, how it works, and what makes it distinctive.

---

## What Is This Product?

A **professional-grade rental property investment analyzer** built specifically for the **Israeli real estate market**. It allows an investor or advisor to model a full property deal — from initial acquisition through eventual sale — and get instant, rigorous answers to:

- Is this deal worth pursuing?
- What are the real returns (cash-on-cash, IRR, equity multiple)?
- How does this mortgage structure affect my long-term position?
- What happens to my returns if rent drops, interest rates rise, or expenses spike?
- How do different holding periods compare?
- What is the maximum I can pay for a property and still hit my return target?

It is both a **Streamlit web app** (interactive, visual, client-facing) and a **command-line tool** for scripted/batch analysis. All deal configurations are saved as JSON files and can be reloaded at any time.

---

## Primary Use Cases

| User | How They Use It |
|------|----------------|
| Real estate investor | Model a specific property, stress-test returns, decide whether to buy |
| Mortgage advisor | Show clients the full financial impact of different mortgage structures (tracks, rates, grace periods, prepayments) |
| Both | Compare financing options side-by-side; find the optimal mortgage mix for a target return |

---

## Core Capabilities

### 1. Israeli Multi-Track Mortgage Engine

This is the product's primary differentiator. Israeli mortgages are composed of multiple parallel "tracks" (מסלולים), each with its own rate type, repayment method, and rules. The engine:

- Supports **up to 3 concurrent tracks** per deal
- **Enforces Bank of Israel regulations**: at least 1/3 of the mortgage must be fixed-rate; variable rate cannot exceed 2/3
- Shows real-time compliance status as the advisor/investor configures the mortgage

**Track types supported:**
- Fixed Unlinked (קל"צ / Kalatz) — most common fixed-rate track
- Fixed CPI-Linked (צמוד) — principal indexed to CPI
- Prime Rate (פריים) — floating, tied to Bank of Israel base rate
- Variable Linked (1Y / 2Y / 5Y / 10Y reset) — CPI-indexed with periodic rate resets
- Variable Unlinked (5Y reset)

**Repayment methods:**
- Spitzer (שפיצר / annuity) — equal monthly payments, front-loaded interest
- Equal Principal (קרן שווה) — declining payments over time
- Bullet (בלון) — interest-only during loan, full principal at maturity

**Advanced features per track:**
- **Grace periods** — either interest-only (no principal) or full deferral (interest capitalizes into balance)
- **Scheduled rate changes** — model future rate resets or renegotiations
- **Prepayments** — specify month, amount, and whether to reduce the term or reduce the monthly payment
- **CPI indexation** — monthly principal adjustment for CPI-linked tracks

The engine runs a true **month-by-month amortization simulation** for each track, combining all tracks into a unified schedule. This produces the exact interest paid, principal outstanding, and total debt service for every month of the loan — not estimates.

---

### 2. Financial Metrics — Instant Deal Scoring

After entering a deal, the product computes a full set of standard real estate investment metrics and benchmarks each one against industry thresholds (Poor / Fair / Good / Excellent).

**Year 1 Snapshot Metrics:**
| Metric | What It Answers |
|--------|----------------|
| NOI (Net Operating Income) | Annual profit before debt service |
| Cap Rate | Return if purchased all-cash; property quality benchmark |
| Cash-on-Cash Return (CoC) | Annual cash return on actual equity invested |
| DSCR (Debt Service Coverage Ratio) | Safety margin — can income service the mortgage? |
| GRM (Gross Rent Multiplier) | Quick valuation sanity check |
| Break-Even Ratio | What % of potential income is consumed by fixed obligations |
| ROE (Year 1) | Cash return relative to current equity |

**Lifecycle / Advanced Metrics:**
| Metric | What It Answers |
|--------|----------------|
| IRR (Internal Rate of Return) | Total annualized return including sale proceeds |
| NPV (Net Present Value) | Absolute value created vs. required return rate |
| Equity Multiple | Total cash returned per ₪ invested |
| Average ROE | Return on equity over entire hold period |
| Equity Buildup | How much comes from appreciation vs. principal paydown |

---

### 3. Multi-Year Pro-Forma Projections

The product projects the deal year-by-year for up to 30 years:

- Income grows at a configured annual rent increase rate
- Fixed expenses (tax, insurance) compound with inflation
- Variable expenses (maintenance, management, CapEx reserve) scale with effective gross income
- Loan balance decreases per the precise amortization schedule
- Property value appreciates at the configured rate
- Equity = property value − remaining loan balance
- Terminal sale proceeds net of selling costs are included in the final year's cash flow

The output is a **formatted pro-forma table** at key milestones (Year 0, 1, 5, 10, hold period end) with a CSV download for further analysis.

---

### 4. Sensitivity & Scenario Analysis

**Two-Variable Sensitivity Heatmap**

Pick any two variables and see how a target metric responds across their ranges. Example: how does IRR change as both interest rate and purchase price vary? Outputs a color-coded heatmap.

Variables available: purchase price, monthly rent, vacancy rate, interest rate, appreciation rate, expense growth, rent growth, down payment, property tax, insurance.

Target metrics: IRR, Cash-on-Cash, Cap Rate, DSCR, Cash Flow.

**Pessimistic / Base / Optimistic Scenario Comparison**

Three pre-built scenarios (each adjusting appreciation, rent growth, expense growth, vacancy, and interest rate together) shown side-by-side in a table and bar chart, comparing: IRR, CoC, DSCR, Equity Multiple, NOI, Cash Flow.

Also includes a **stress test** that finds the break-even vacancy rate and maximum expense overhead the deal can absorb before going cash-flow negative.

---

### 5. Deal Optimizer Functions

Beyond analysis, the product has built-in optimization utilities:

- **Break-even rent calculator** — binary search for the minimum monthly rent needed to avoid negative cash flow
- **Maximum purchase price calculator** — binary search for the highest price still hitting a target CoC
- **Holding period comparison** — runs IRR, Equity Multiple, NPV, CoC, DSCR, Avg ROE across multiple hold periods (e.g., 5y vs. 10y vs. 15y vs. 20y) to find the optimal exit window
- **Financing option comparison** — side-by-side analysis of different mortgage structures on the same property

---

### 6. Income & Expense Modeling

**Income flow:**
```
Gross Potential Rent (GPR)
+ Other Income (parking, storage, laundry, pet fees, utilities)
− Vacancy Loss (% of GPR)
− Credit Loss (% of GPR)
= Effective Gross Income (EGI)
− Operating Expenses
= NOI
− Debt Service
= Pre-Tax Cash Flow
```

**Expense categories:**
- Fixed: property tax, insurance, HOA, landlord-paid utilities (all grown annually with inflation)
- Variable (% of EGI): maintenance, property management, CapEx reserve (auto-grown with EGI)
- Itemized other expenses: can be specified per-unit or flat, monthly or annual or % of income

**Dual-input widgets** in the UI allow any input to be entered as either a percentage or an absolute amount, with instant conversion shown — making it intuitive for advisors configuring deals for clients.

---

## The UI (Streamlit Web App)

The web app has a tabbed input layout and a results panel that opens after running the analysis.

**Input tabs:** Property → Financing → Income → Expenses → Market

**Results tabs:**
- **Overview** — color-coded metric cards, sorted best-to-worst, each with a tooltip showing formula, definition, and benchmark thresholds
- **Visualizations** — interactive Plotly charts: NOI/Cash Flow/DSCR trend lines, ROE over time with target benchmarks, wealth-building stacked area chart (property value / equity / loan balance)
- **Pro Forma** — key-year table with CSV download
- **Sensitivity** — two-variable heatmap + scenario comparison chart and table

The **regulatory compliance widget** in the financing section shows the fixed/variable ratio in real time as the mortgage is configured, turning green when compliant and red when not — giving advisors immediate feedback on whether a proposed structure is legal.

---

## CLI / Scripting

Three command-line scripts for programmatic or batch use:

- `analyze_deal.py <deal.json>` — prints a full Rich-formatted terminal report (financing tracks, metrics table, pro-forma summary)
- `amortization_schedule.py <deal.json>` — prints month-by-month amortization per track and combined; supports filtering by month range, events-only view, and specific track
- `export_schedule_csv.py <deal.json>` — exports full amortization schedule to CSV

---

## Current Market Focus

The product is currently calibrated for **Israel**:
- Monetary amounts in Israeli Shekels (₪)
- Mortgage tracks and rules based on **Bank of Israel regulations**
- Example deal (`itzhak_navon_21.json`) models a real Israeli property at ₪3,756,000 with a Kalatz + Prime mortgage combination

The underlying financial engine is generic and could be adapted to other markets, but the mortgage modeling is deeply Israeli in design.

---

## Technical Stack (for context)

| Component | Technology |
|-----------|-----------|
| Web UI | Streamlit |
| Financial math | numpy-financial (IRR, NPV, PMT) |
| Data modeling | Pydantic v2 |
| Charts | Plotly |
| CLI output | Rich |
| Data/pro-forma | Pandas |
| Logging | Loguru (calculation audit trail) |

All deal data is stored locally as JSON files — no database, no external API dependencies. The product is self-contained and runs locally.

---

## What the Product Does NOT Currently Do

- No live data feeds (no Zillow, no Bank of Israel rate API) — all inputs are manual
- No portfolio dashboard (placeholder exists, not yet built)
- No multi-property comparison in the UI (only through CLI scripts)
- No user accounts or cloud sync — local-only
- No US-style mortgage products (ARM, FHA, VA, etc.) — input fields exist in the data model but the calculator is Israeli-track-centric
- No tax calculation (pre-tax cash flows only)

---

## Potential Value Proposition for Mortgage Advisors

1. **Client education tool** — show a client exactly what their monthly payments look like across all tracks, how the balance evolves, and what total interest they will pay over the life of the loan
2. **Compliance guardrail** — instantly see if a proposed mortgage structure violates Bank of Israel regulations before presenting it to a client
3. **Comparative analysis** — run the same property with two different mortgage structures and show the client which one produces better long-term returns
4. **Deal qualification** — quickly determine if a property's DSCR is high enough to comfortably service a given mortgage
5. **Prepayment modeling** — show clients the concrete impact (in total interest saved and term reduction) of making a one-time or recurring prepayment

## Potential Value Proposition for Real Estate Investors

1. **Full-lifecycle return modeling** — not just cap rate; true IRR including the sale, accounting for mortgage paydown, appreciation, and all expenses
2. **Optimal hold period** — data-driven answer to "when should I sell?"
3. **Risk stress testing** — understand how bad things need to get before the deal turns negative
4. **Mortgage structure optimization** — find the track mix that maximizes cash flow vs. total interest paid
5. **Offer price discipline** — know the maximum you can pay for a property and still hit your target return
