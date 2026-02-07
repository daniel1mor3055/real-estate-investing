Got it — longer, more vivid, “IRR-style” tooltips for **each KPI tile** in your screenshot.

---

## NOI (Net Operating Income)

**What it measures:** NOI is the property’s **pure operating profit** — how much money the building itself produces **before** you think about the mortgage or taxes. It’s the “engine power” of the property. 

**How to think about it:**
Imagine the property is a little business (like a coffee shop). NOI answers: *“After I pay staff, supplies, rent utilities, repairs, management… how much profit does the shop generate?”* But it **ignores** how you financed it.

**Mini example:**

* Rent collected (after vacancy): **$200,000**
* Operating expenses: **$120,000**
* **NOI = $80,000**
  That $80k is the building’s “operating profit” — whether you paid all-cash or used a loan.

---

## Cap Rate (Capitalization Rate)

**What it measures:** Cap Rate is the property’s **unlevered yield** — the return you’d get **if you bought it with all cash**, based on NOI. 

**How to think about it:**
Cap Rate is like the property’s “price tag interest rate.” It helps answer: *“Am I paying a reasonable price for the income this building produces?”* It’s heavily used to compare similar properties in the same market. 

**Mini example:**

* NOI: **$80,000**
* Price: **$2,000,000**
* Cap Rate = 80,000 / 2,000,000 = **4%**
  Meaning: *if you bought it all-cash, the building “yields” about 4% per year from operations.*

---

## Cash Flow (Annual Pre-Tax Cash Flow)

**What it measures:** Cash Flow is the **real money left in your pocket** after the building runs **and** after you pay the mortgage (principal + interest). 

**How to think about it:**
If NOI is the engine, Cash Flow is what’s left **after the bank takes its cut**. It answers: *“After everything is paid, do I personally take money home each year, or do I need to feed the property money?”* 

**Mini example:**

* NOI: **$80,000**
* Annual mortgage payments: **$95,000**
* Cash Flow = 80,000 − 95,000 = **–$15,000**
  Meaning: you’re short $15k per year — you must cover it from your own funds.

---

## CoC Return (Cash-on-Cash Return)

**What it measures:** CoC tells you the **annual cash return** on the **actual cash you invested** (down payment, closing costs, rehab, etc.). 

**How to think about it:**
CoC answers a very practical investor question: *“If I put in $1 today, how many cents do I get back this year as spendable cash?”* It’s like the deal’s “Year-1 paycheck” on your equity. 

**Mini example:**

* Total cash you invested: **$500,000**
* Annual cash flow: **$25,000**
* CoC = 25,000 / 500,000 = **5%**
  Meaning: your invested cash is producing about 5% per year in cash you can actually take out (before tax).

---

## DSCR (Debt Service Coverage Ratio)

**What it measures:** DSCR is the property’s **loan safety cushion** — how comfortably the building’s NOI can pay the mortgage payments. 

**How to think about it (very vivid):**
Picture the mortgage as a monthly “boss fight” you must win. DSCR tells you how strong your character is going into that fight:

* **DSCR = 1.0x** → you barely survive. You cover the mortgage exactly, **no room for error**. 
* **DSCR = 1.25x** → you have a 25% cushion if rents drop or expenses spike. 
* **DSCR < 1.0x** → the property can’t pay the mortgage from operations; you must subsidize it.

**Mini example:**

* NOI: **$80,000**
* Annual mortgage payments: **$100,000**
* DSCR = 80,000 / 100,000 = **0.80x**
  Meaning: the property covers only 80% of the loan payment — it’s underwater from a lender-risk perspective.

---

## Break Even Ratio

**What it measures (plain-English):** Break Even Ratio asks: **“How close am I to the line where income just barely covers all required costs?”** It’s a *survival metric* — similar spirit to DSCR’s “1.0x is break-even” concept. 

**How to think about it (why your 129.98% looks scary):**
This ratio is easiest to read like a “budget pie”:

* **100%** = every dollar of income is used to pay bills → **zero** leftover
* **< 100%** = you have breathing room
* **> 100%** = your costs are bigger than your income → you must feed the property money

**Mini example:**
Say the property brings in **$100,000** of effective income.

* If all-in costs are **$85,000**, break-even ratio is **85%** → you keep ~15% cushion.
* If all-in costs are **$130,000**, break-even ratio is **130%** → you are short ~30% of your income.

**In other words:** a **129.98%** break-even ratio means: *“For every $1.00 the property earns, it needs about $1.30 to cover costs.”* That’s why it’s flagged “poor” in the UI.

*(Note: your doc explicitly defines the break-even idea via DSCR=1.0 (“no room for error”). The Break Even **ratio** is the same intuition, just expressed as “cost pressure” instead of “coverage strength.” )*

---

## Equity Multiple (EM)

**What it measures:** Equity Multiple is the simplest “money machine” metric: **how many dollars you got back for each $1 you invested**, across the entire deal (cash flows + sale). 

**How to think about it:**
If you put a dollar into a vending machine, EM answers: *“How many dollars came out before the machine shut down?”* It ignores *speed* (time) — it only measures *total multiplication*. 

**Mini example:**

* You invest **$1,000,000** total equity over time
* Over the hold + sale, you receive **$2,990,000** back
* EM = 2,990,000 / 1,000,000 = **2.99x**
  Meaning: you got your original $1 back, plus $1.99 profit — total $2.99 per $1 invested.

**Important nuance (super common confusion):**
If you have negative cash flow years (you inject money), that counts as **additional equity invested** (it increases the denominator), not “negative distributions.” 

---

## IRR (Internal Rate of Return)

**What it measures:** IRR is the deal’s **annualized growth rate** — the single “interest rate” that best describes how fast your invested money grew, considering *when* cash flows happened and the final sale. 

**How to think about it (IRR-style):**
IRR turns the whole deal into a “magic bank account” story:

* You deposit money when you invest.
* You withdraw money when the property pays you cash flow.
* You withdraw a big amount at the sale.
  IRR is the interest rate where, after the last withdrawal, the account ends at **exactly $0** — meaning the deal’s cash flows perfectly match that rate.

**Mini example:**
If IRR is **7%**, it means: *“The deal behaved like your invested capital was compounding at ~7% per year, given the timing of all cash in/out.”* 

---

If you want, paste the exact list of metrics your UI supports (maybe you have more tiles beyond this screenshot), and I’ll format these into **tooltip-ready strings** (short title + longer body + “example” line), consistent tone and length across all of them.
