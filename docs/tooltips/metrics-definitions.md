# Real Estate Investment Metrics: Comprehensive Definitions

> **Purpose**: This document provides detailed, plain-English explanations for all financial metrics used in the Real Estate Investment application. Use this as the authoritative reference when implementing tooltips, documentation, and user-facing explanations.

---

## Table of Contents

1. [NOI — Net Operating Income](#1-noi--net-operating-income)
2. [Cap Rate — Capitalization Rate](#2-cap-rate--capitalization-rate)
3. [Cash Flow (Year 1)](#3-cash-flow-year-1)
4. [CoC Return — Cash-on-Cash Return](#4-coc-return--cash-on-cash-return)
5. [DSCR — Debt Service Coverage Ratio](#5-dscr--debt-service-coverage-ratio)
6. [GRM — Gross Rent Multiplier](#6-grm--gross-rent-multiplier)
7. [IRR — Internal Rate of Return](#7-irr--internal-rate-of-return)
8. [NPV — Net Present Value](#8-npv--net-present-value)
9. [Equity Multiple](#9-equity-multiple)
10. [Break-even Ratio](#10-break-even-ratio)
11. [Deal Score](#11-deal-score)
12. [ROE — Return on Equity](#12-roe--return-on-equity)

---

## Metric Classification Framework

Understanding how metrics relate to each other:

### Property Metrics (Unlevered)
These describe the property itself, independent of financing:
- **NOI** / **Cap Rate** / **GRM**

### Deal Metrics (Levered)
These describe the deal with financing included:
- **Cash Flow** / **CoC** / **DSCR**

### Lifecycle Metrics
These describe the entire investment over time, including exit:
- **IRR** / **NPV** / **Equity Multiple**

### Risk/Resilience Metrics
These describe downside protection and cushion:
- **Break-even Ratio** / **DSCR**

### Summary Metrics
These are composite scores:
- **Deal Score** / **ROE**

---

## 1) NOI — Net Operating Income

### What It Means (Plain English)
NOI is the property's profit from operations before any financing decisions. It's the money the building produces after you collect income and pay normal operating bills (taxes, insurance, utilities you cover, maintenance, management, etc.), but before you pay the mortgage. The main point of NOI is that it describes the property itself, not the investor's loan, so it's the backbone of property valuation and lender underwriting.

### Formula
```
NOI = Gross Operating Income - Operating Expenses
```

Where:
- **Gross Operating Income** = Potential Gross Income - Vacancy Loss
- **Operating Expenses** = Property taxes, insurance, utilities, maintenance, management fees, etc.

### What NOI Usually Excludes (Important for Consistency)
Most standard definitions explicitly exclude:
- ❌ **Principal and Interest** (debt service)
- ❌ **Capital Expenditures** (CapEx) like roof replacement, major systems, and other "big replacements"

**Note**: Some models include a CapEx reserve as an operating-like expense to avoid overstating profitability; if you do this, your tooltip should be explicit about it.

### Common Pitfalls Users Misunderstand
- ❌ Treating mortgage payments as an "expense" in NOI (it's not, by definition)
- ❌ Mixing one-time items (a rare repair) into "stabilized NOI" without labeling it
- ❌ Confusing "gross income" with "net income"

### Tooltip-Ready (2–3 Sentences)
**NOI is the property's annual profit after operating expenses but before the mortgage and taxes. It's the core measure of operational performance and is used for cap rate valuation and lender coverage tests.**

### Current Benchmarks
- **Low**: $10,000
- **Target**: $20,000
- **High**: $40,000

### Higher Is Better
✅ Yes

---

## 2) Cap Rate — Capitalization Rate

### What It Means (Plain English)
Cap rate is a quick way of saying: "If I bought this property with cash, what annual yield would the NOI imply at this price?" It's calculated from a single year of (ideally stabilized) NOI relative to the property's value/price, so it's best viewed as a pricing/valuation shortcut, not the full investment return (because it ignores financing and future growth).

### Formula
```
Cap Rate = NOI ÷ Property Value
```

### Why It's Useful
Cap rate helps you compare similar assets in the same market: if two buildings have similar risk and quality, the one with the higher cap rate generally gives you more NOI per dollar of price (though higher cap rates can also signal higher risk).

### Common Pitfalls
- ❌ Using cap rate to compare totally different property types/markets without context
- ❌ Using "in-place" NOI that's not stabilized (e.g., temporary vacancy) and treating it as comparable
- ❌ Forgetting that cap rate ignores financing and future value appreciation

### Tooltip-Ready (2–3 Sentences)
**Cap rate is NOI divided by property value — an unlevered yield implied by the current income and price. It's mainly a market comparison and valuation tool, not a full return metric.**

### Current Benchmarks
- **Low**: 4%
- **Target**: 6.5%
- **High**: 9%

### Higher Is Better
✅ Yes (generally, though context matters — very high cap rates may signal higher risk)

---

## 3) Cash Flow (Year 1)

### What It Means (Plain English)
Year-1 cash flow is how much money is left after you pay operating expenses and the mortgage (principal + interest). It's the "money in your pocket" number investors care about because it shows whether the property can support itself and produce spendable income early on.

### Formula
```
Cash Flow = NOI - Debt Service (Principal + Interest)
```

**Alternative (if including reserves)**:
```
Cash Flow = NOI - Debt Service - CapEx Reserves
```

### Key Definition Choice You Must Be Consistent About
When people say "cash flow," they often mean **before-tax cash flow** (i.e., they haven't subtracted income taxes). Some analyses also subtract reserves (like CapEx reserves) to be conservative.

**⚠️ Your tooltip should clearly state whether your app's cash flow is:**
- **Pre-tax** or post-tax
- Whether **reserves/CapEx** are included in expenses

### Common Pitfalls
- ❌ Confusing "cash flow" with NOI (cash flow is levered; NOI is unlevered)
- ❌ Forgetting that principal paydown is not "lost" — it builds equity even though it reduces cash flow
- ❌ Treating negative cash flow as automatically bad (some value-add strategies accept negative early cash flow)

### Tooltip-Ready (2–3 Sentences)
**Year-1 cash flow is the property's remaining pre-tax profit after operating expenses and debt payments are made. Positive cash flow generally means the deal can support itself day-to-day.**

### Current Benchmarks
- **No current benchmarks defined**

### Higher Is Better
✅ Yes

---

## 4) CoC Return — Cash-on-Cash Return

### What It Means (Plain English)
Cash-on-cash return answers: "What annual cash yield am I earning on the cash I actually put into the deal?" It's calculated by dividing annual pre-tax cash flow by the investor's total cash invested (down payment + closing costs + initial rehab, etc.). It's popular because it's intuitive and directly tied to cash you deployed.

### Formula
```
CoC Return = Annual Pre-Tax Cash Flow ÷ Total Cash Invested
```

Where:
- **Total Cash Invested** = Down payment + closing costs + initial improvements/rehab

### Why It's Useful
CoC is great for comparing deals when your main goal is income and you're looking at leveraged purchases. It explicitly reflects the impact of financing (unlike cap rate).

### Common Pitfalls
- ❌ Comparing CoC returns across deals with wildly different risk and debt terms without also checking DSCR
- ❌ Treating CoC like a "total return" metric (it ignores appreciation and sale proceeds)
- ❌ Using inconsistent definitions of "total cash invested"

### Tooltip-Ready (2–3 Sentences)
**Cash-on-cash return is annual pre-tax cash flow ÷ total cash invested. It measures the first-year cash yield on your actual out-of-pocket investment and is heavily influenced by leverage.**

### Current Benchmarks
- **Low**: 6%
- **Target**: 10%
- **High**: 15%

### Higher Is Better
✅ Yes

---

## 5) DSCR — Debt Service Coverage Ratio

### What It Means (Plain English)
DSCR is a safety metric: it tells you how comfortably the property's NOI can cover the mortgage payment. A DSCR of 1.0 means NOI exactly equals debt service; above 1.0 means there's a cushion; below 1.0 means the property doesn't generate enough NOI to pay the loan from operations. Lenders rely on DSCR to judge default risk.

### Formula
```
DSCR = NOI ÷ Annual Debt Service
```

### Interpretation
- **DSCR < 1.0**: Property doesn't generate enough to cover the mortgage (red flag)
- **DSCR = 1.0**: Break-even (risky)
- **DSCR > 1.0**: Cushion exists (safer)
- **DSCR ≥ 1.25**: Typical lender minimum
- **DSCR ≥ 1.5**: Strong coverage

### Why It Matters to Users
DSCR helps explain "risk." Two deals can have similar returns, but the one with the stronger DSCR is generally more resilient to vacancy and expense surprises.

### Common Pitfalls
- ❌ Mixing inconsistent definitions of NOI or debt service (interest-only vs amortizing)
- ❌ Confusing DSCR (a coverage ratio) with profitability (you can have DSCR > 1 and still have low cash flow, depending on reserves/other items)

### Tooltip-Ready (2–3 Sentences)
**DSCR is NOI ÷ annual debt service — how many times the property's operating income covers the mortgage payments. Higher DSCR means more cushion and generally lower lender/investor risk.**

### Current Benchmarks
- **Low**: 1.2x
- **Target**: 1.5x
- **High**: 2.0x

### Higher Is Better
✅ Yes

---

## 6) GRM — Gross Rent Multiplier

### What It Means (Plain English)
GRM is a fast, rough valuation screen: it compares the property's price to its gross annual rent (before vacancy and expenses). Lower GRM usually implies "cheaper for the rent you're getting," but it's deliberately simplistic and should never be the final decision tool.

### Formula
```
GRM = Property Price ÷ Gross Annual Rent
```

### Why It's Useful
GRM is quick for scanning listings and comparing similar rentals, especially when you don't have full expense detail yet.

### Common Pitfalls
- ❌ Forgetting GRM ignores expenses — two properties with identical GRM can have very different NOI
- ❌ Using GRM across different markets without context (expensive markets naturally have higher GRMs)
- ❌ Making investment decisions based solely on GRM

### Tooltip-Ready (2–3 Sentences)
**GRM is price ÷ gross annual rent. It's a quick screening metric that ignores vacancy and expenses, so it's best used only for early comparisons.**

### Current Benchmarks
- **Low**: 4 (better value)
- **Target**: 8
- **High**: 12

### Lower Is Better
✅ Yes (lower GRM = better value per rent dollar)

---

## 7) IRR — Internal Rate of Return

### What It Means (Plain English)
IRR is the annualized return rate that makes the present value of all cash flows (including the sale) equal to the initial investment — in other words, it's the discount rate where NPV = 0. IRR is powerful because it accounts for timing: getting $10k back next year is treated as better than getting $10k back in year 10.

### Formula
IRR is the rate `r` that solves:
```
NPV = 0 = -Initial Investment + Σ(Cash Flow_t / (1 + r)^t) + Sale Proceeds / (1 + r)^n
```

### Why It's Useful
IRR is great for comparing deals with different cash flow patterns and exit outcomes because it compresses the whole lifecycle into one time-weighted annual rate.

### Known Limitations / Pitfalls
- ⚠️ IRR can be misleading if used alone: it can "look good" when there are early cash flows even if total profit isn't huge
- ⚠️ Unusual cash flow patterns can produce weird interpretations or multiple IRRs
- ⚠️ IRR doesn't show the magnitude of returns (a 20% IRR on $10k is different from 20% on $1M)

**Best Practice**: Many professional writeups recommend pairing IRR with equity multiple/NPV so you see both speed and magnitude of returns.

### Tooltip-Ready (2–3 Sentences)
**IRR is the annualized return rate that makes the investment's NPV equal zero, considering all cash flows and the sale. It's a time-weighted metric that's best read alongside equity multiple or NPV.**

### Current Benchmarks
- **Low**: 8%
- **Target**: 15%
- **High**: 25%

### Higher Is Better
✅ Yes

---

## 8) NPV — Net Present Value

### What It Means (Plain English)
NPV converts all future cash flows into today's dollars using a discount rate (your required return). Then it subtracts the initial investment. If NPV is positive, the deal is expected to beat your required return; if it's negative, it's expected to fall short (given your assumptions and discount rate).

### Formula
```
NPV = Σ(Cash Flow_t / (1 + discount_rate)^t) + Sale Proceeds / (1 + discount_rate)^n - Initial Investment
```

### Why It's Useful
NPV is a direct "value creation" measure: it tells users not just "what percent," but how many dollars of value a deal creates above their hurdle rate. It's especially helpful when comparing a smaller deal vs a larger one.

### Common Pitfalls
- ❌ Users treating NPV like a universal truth: it heavily depends on the chosen discount rate
- ❌ Comparing NPV across deals of different size without also showing something like IRR (rate) or NPV per dollar invested
- ❌ Not understanding that NPV answers "value vs my hurdle rate," not "what's my return rate?"

### Tooltip-Ready (2–3 Sentences)
**NPV is the value today of all future cash flows discounted at your required return, minus the initial investment. Positive NPV means the deal is expected to outperform your hurdle rate.**

### Current Benchmarks
- **No current benchmarks defined**

### Higher Is Better
✅ Yes (positive NPV = value creation; negative NPV = destroys value)

---

## 9) Equity Multiple

### What It Means (Plain English)
Equity multiple answers: "How many total dollars do I get back for every $1 I invest?" It divides total cash returned over the entire hold (operating cash flow + sale proceeds) by total equity invested. It's easy to understand because it focuses on total money back, not annualized rates.

### Formula
```
Equity Multiple = Total Cash Returned ÷ Total Equity Invested
```

Where:
- **Total Cash Returned** = Sum of all operating cash flows + net sale proceeds
- **Total Equity Invested** = Down payment + closing costs + improvements

### What It Does Not Tell You
Equity multiple does not care when you get the cash back. A deal that returns 2.0x over 20 years and 2.0x over 5 years has the same equity multiple — that's why people pair it with IRR.

### Interpretation
- **< 1.0x**: You're losing money
- **1.0x**: Break-even (you got your money back, but no profit)
- **1.5x–2.0x**: Solid returns
- **2.0x+**: Strong returns
- **3.0x+**: Exceptional returns

### Tooltip-Ready (2–3 Sentences)
**Equity multiple is total cash returned ÷ total equity invested. It shows overall cash profit but doesn't account for how long it takes — pair it with IRR for timing.**

### Current Benchmarks
- **Low**: 1.5x
- **Target**: 2.0x
- **High**: 3.0x

### Higher Is Better
✅ Yes

---

## 10) Break-even Ratio

### What It Means (Plain English)
Break-even ratio estimates what percentage of the property's income is required just to cover operating expenses and debt payments. Put differently: the lower the break-even ratio, the more the deal can tolerate vacancy or rent drops before it stops paying for itself.

### Formula
```
Break-even Ratio = (Operating Expenses + Debt Service) ÷ Gross Operating Income
```

**Related concept**: Break-even occupancy (the occupancy level needed to cover costs), which is commonly computed as:
```
Break-even Occupancy = (OpEx + Debt Service) ÷ Potential Gross Income
```

### Interpretation
- **< 70%**: Very safe (lots of cushion)
- **70%–85%**: Good cushion
- **85%–95%**: Moderate risk
- **> 95%**: High risk (little room for vacancy/problems)
- **> 100%**: Deal doesn't support itself

### Common Pitfalls
- ❌ Confusing break-even ratio with break-even occupancy (they're closely related but expressed differently)
- ❌ Not accounting for realistic vacancy rates when evaluating the ratio

### Tooltip-Ready (2–3 Sentences)
**Break-even ratio is (operating expenses + debt service) ÷ gross operating income. Lower is safer because the property needs less income to cover all required payments.**

### Current Benchmarks
- **Low**: 70% (safer)
- **Target**: 85%
- **High**: 95% (riskier)

### Lower Is Better
✅ Yes (lower = more safety cushion)

---

## 11) Deal Score

### What It Means (Plain English)
Deal Score is not a universal industry metric — it's a product/UX metric: a single 0–100 score made by combining multiple KPIs into a weighted composite. Its purpose is to help users quickly rank deals and understand "overall quality" based on their goals (cash-flow-first vs appreciation-first, etc.).

### How It's Calculated
Deal Score depends on:
1. **Which metrics you include** (e.g., CoC, IRR, DSCR, Cap Rate, etc.)
2. **How you normalize them** (converting raw values to 0–100 scale)
3. **Your chosen weights** (how much each metric contributes to final score)

### How to Explain It So Users Trust It
- ✅ Make it explicit that Deal Score is configurable and depends on user goals
- ✅ Show transparency: let users see the underlying metrics driving the score
- ✅ Allow users to adjust weights based on their investment strategy

### Common Use Cases
- Quickly ranking/filtering multiple deals
- Understanding at-a-glance quality
- Comparing deals with different characteristics

### Tooltip-Ready (2–3 Sentences)
**Deal Score is a weighted composite that summarizes multiple metrics (returns + safety) into a single 0–100 rating. Use it to compare deals quickly, then drill into the underlying KPIs to see what's driving the score.**

### Current Benchmarks
- **Low**: 40
- **Target**: 60
- **High**: 80

### Higher Is Better
✅ Yes

---

## 12) ROE — Return on Equity

### What It Means (Plain English)
In real estate, ROE is about how hard your current trapped equity is working. As time passes, you often build equity through appreciation and principal paydown; ROE helps answer: "Given how much equity I now have in the property, is the income (and/or total return) still worth keeping this asset?" That's why ROE is commonly used in hold vs sell (or refinance) decisions.

### Formula (Income-Focused Version)
```
ROE = Annual Cash Flow ÷ Current Equity
```

Where:
- **Current Equity** = Current Property Value - Outstanding Loan Balance

**Alternative (Total Return Version)**:
```
ROE = (Cash Flow + Appreciation + Principal Paydown) ÷ Current Equity
```

### Critical Definition Choice (You Must Pick One and State It)
- **Income-focused**: ROE = annual cash flow ÷ current equity
- **Total return**: ROE includes appreciation and principal paydown

**⚠️ Both can be defensible, but mixing them without labeling will confuse users.**

### Why It Matters
- Helps with **hold vs sell decisions**: If ROE drops significantly (e.g., from 12% to 4%), you might get better returns by selling and redeploying capital
- Highlights when equity has grown but cash flow hasn't kept pace
- Useful for refinance decisions (pulling equity out)

### Common Pitfalls
- ❌ Confusing ROE with CoC (CoC is based on initial investment; ROE is based on current equity)
- ❌ Not clarifying which version of ROE you're using
- ❌ Ignoring transaction costs when deciding to sell based on ROE

### Tooltip-Ready (2–3 Sentences)
**ROE measures how efficiently the property's current equity is generating returns (often annual cash flow divided by current equity). It's useful for hold/sell decisions when equity has grown but cash flow hasn't.**

### Current Benchmarks
- **No current benchmarks defined** (typically evaluated relative to alternative investment opportunities)

### Higher Is Better
✅ Yes (but context matters — compare to alternative investment returns)

---

## Implementation Guidelines

### For Tooltips
1. **Use the "Tooltip-Ready" text** as the base for user-facing explanations
2. **Add "Includes/Excludes" clarifications** where relevant (especially NOI, Cash Flow, ROE)
3. **Show the formula** if space allows (helps advanced users)
4. **Include visual gauges** based on the defined benchmarks

### For Documentation
1. Reference this file as the authoritative source
2. Keep definitions consistent across all UI elements
3. Update benchmarks as market conditions change

### For Data Models
Store metric metadata in a structured format:
```json
{
  "NOI": {
    "name": "Net Operating Income",
    "shortName": "NOI",
    "definition": "The property's annual profit after operating expenses but before the mortgage and taxes.",
    "formula": "Gross Operating Income - Operating Expenses",
    "includes": ["Property taxes", "Insurance", "Maintenance", "Management fees"],
    "excludes": ["Principal and Interest", "Capital Expenditures"],
    "higherIsBetter": true,
    "benchmarks": {
      "low": 10000,
      "target": 20000,
      "high": 40000
    },
    "category": "property_unlevered"
  }
}
```

---

## Key Principle to Prevent Confusion

**"One Sentence" Distinction:**

- **NOI / Cap Rate / GRM** → describe the **property** (mostly independent of financing)
- **Cash Flow / CoC / DSCR** → describe the **deal with financing** (levered reality)
- **IRR / NPV / Equity Multiple** → describe the **whole lifecycle** (including the exit)
- **Break-even Ratio** → describes **resilience / downside cushion**
- **Deal Score** → your **product summary metric** (depends on your chosen framework)

**Most Important Implementation Tip**: For any metric that has ambiguity (NOI, Cash Flow, ROE, Break-even), add a tiny "Includes: … / Excludes: …" note in the tooltip. That's where most apps accidentally mislead users.

---

## Document Metadata

- **Created**: 2026-02-06
- **Last Updated**: 2026-02-06
- **Version**: 1.0
- **Maintained By**: Real Estate Investment Application Team
- **Related Files**: 
  - `src/models/metrics.py` (metric calculations)
  - `TICKET-20260202-202528-2026-02-02-add-metric-tooltips-with-explanations.md` (implementation ticket)
