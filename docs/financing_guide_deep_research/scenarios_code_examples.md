Got it. Also: the tool is still warning that **some older uploaded files expired**, but the PDF you just re-uploaded is available and I’m using its `amortization_schedule` function as the base.

Below you’ll find:

1. A **cleaned, runnable version** of the PDF’s `amortization_schedule` (same logic, just formatted).
2. **One code snippet per scenario** (1→5), each generating a monthly table with payment / interest / principal / balance.
3. For Scenario 5 (multi-events), I include a small **event-capable wrapper** (an extension of the PDF function) to support **multiple rate changes + multiple prepays** cleanly.

---

## Common setup (use once)

```python
import pandas as pd
import numpy as np
import numpy_financial as npf
from typing import List, Dict, Optional

def amortization_schedule(
    amount: float,
    annual_rate: float,
    months: int,
    method: str,
    index_rate: float = 0.0,
    grace_period: int = 0,
    grace_type: str = "none",   # "none" | "interest_only" | "full"
    rate_change_month: Optional[int] = None,
    rate_change_delta: float = 0.0,
    prepay_month: Optional[int] = None,
    prepay_amount: float = 0.0,
    prepay_full: bool = False,
    prepay_option: str = "term" # "term" (shorten term) | "payment" (reduce payment)
) -> List[Dict]:
    """
    Cleaned version of the PDF function:
    Returns list of dict rows: Month, Payment, Interest, Principal, Balance
    """
    method = method.lower()

    monthly_rate = annual_rate / 12.0
    monthly_inflation = (1 + index_rate) ** (1/12.0) - 1.0 if index_rate != 0.0 else 0.0

    schedule = []
    balance = amount
    current_rate = annual_rate
    current_monthly_rate = monthly_rate

    fixed_payment = None
    principal_installment = None

    # Initial payment setup (no grace)
    if method == "spitzer":
        if grace_type == "none" or grace_period == 0:
            # Use numpy-financial to avoid reinventing the annuity wheel:
            fixed_payment = -npf.pmt(rate=current_monthly_rate, nper=months, pv=balance)
    elif method == "equal":
        if grace_type == "none" or grace_period == 0:
            principal_installment = amount / months

    grace_ended = (grace_type == "none" or grace_period == 0)

    m = 1
    while m <= months:
        # Apply interest rate change (month after specified month)
        if rate_change_month is not None and m == rate_change_month + 1:
            current_rate += rate_change_delta
            current_monthly_rate = current_rate / 12.0

            if method == "spitzer":
                remaining = months - (m - 1)
                fixed_payment = -npf.pmt(rate=current_monthly_rate, nper=remaining, pv=balance)

        # Grace: full deferral
        if grace_type == "full" and m <= grace_period:
            if monthly_inflation:
                balance *= (1 + monthly_inflation)
            interest = balance * current_monthly_rate
            balance += interest
            payment = 0.0
            principal_paid = 0.0

        # Grace: interest only
        elif grace_type == "interest_only" and m <= grace_period:
            if monthly_inflation:
                balance *= (1 + monthly_inflation)
            interest = balance * current_monthly_rate
            payment = interest
            principal_paid = 0.0

        else:
            # Grace ended: recompute schedule for remaining term
            if not grace_ended and m == grace_period + 1:
                grace_ended = True
                remaining = months - grace_period
                if method == "spitzer":
                    fixed_payment = -npf.pmt(rate=current_monthly_rate, nper=remaining, pv=balance)
                elif method == "equal":
                    principal_installment = balance / remaining

            # CPI indexation update (before payment)
            if monthly_inflation:
                balance *= (1 + monthly_inflation)
                if method == "spitzer":
                    remaining = months - (m - 1)
                    fixed_payment = -npf.pmt(rate=current_monthly_rate, nper=remaining, pv=balance)
                elif method == "equal":
                    remaining = months - (m - 1)
                    principal_installment = balance / remaining

            if method == "spitzer":
                interest = balance * current_monthly_rate
                payment = float(fixed_payment)
                principal_paid = payment - interest
                principal_paid = max(principal_paid, 0.0)
                balance -= principal_paid

            elif method == "equal":
                interest = balance * current_monthly_rate
                if principal_installment is None:
                    principal_installment = balance / (months - (m - 1))
                principal_paid = float(principal_installment)
                payment = interest + principal_paid
                balance -= principal_paid

            elif method == "bullet":
                interest = balance * current_monthly_rate
                if m < months:
                    payment = interest
                    principal_paid = 0.0
                else:
                    payment = interest + balance
                    principal_paid = balance
                    balance = 0.0
            else:
                raise ValueError("method must be: 'spitzer' | 'equal' | 'bullet'")

        # Prepayment in this month
        if prepay_month is not None and m == prepay_month:
            if prepay_full:
                # pay off remaining balance now
                payment += balance
                principal_paid += balance
                balance = 0.0
            else:
                extra = min(prepay_amount, balance)
                payment += extra
                principal_paid += extra
                balance -= extra

                remaining = months - m
                if remaining > 0 and prepay_option == "payment":
                    if method == "spitzer":
                        fixed_payment = -npf.pmt(rate=current_monthly_rate, nper=remaining, pv=balance)
                    elif method == "equal":
                        principal_installment = balance / remaining

        schedule.append({
            "Month": m,
            "Payment": payment,
            "Interest": interest,
            "Principal": principal_paid,
            "Balance": max(balance, 0.0)
        })

        if balance <= 1e-8:
            break

        m += 1

    return schedule


def to_df(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows).set_index("Month")
    return df.round(2)


def combine_tracks(track_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Align by month, sum payments/interest/principal/balance across tracks.
    For balance, summing is correct (remaining principal total).
    """
    all_months = sorted(set().union(*[df.index for df in track_dfs.values()]))
    aligned = []
    for name, df in track_dfs.items():
        tmp = df.reindex(all_months).fillna(0.0)
        tmp.columns = pd.MultiIndex.from_product([[name], tmp.columns])
        aligned.append(tmp)

    wide = pd.concat(aligned, axis=1)
    total = pd.DataFrame({
        "Payment": wide.xs("Payment", level=1, axis=1).sum(axis=1),
        "Interest": wide.xs("Interest", level=1, axis=1).sum(axis=1),
        "Principal": wide.xs("Principal", level=1, axis=1).sum(axis=1),
        "Balance": wide.xs("Balance", level=1, axis=1).sum(axis=1),
    }, index=all_months).round(2)

    return wide, total
```

---

# Scenario 1 — Single Track, Simple Spitzer

```python
df1 = to_df(amortization_schedule(
    amount=600_000,
    annual_rate=0.035,
    months=25*12,
    method="spitzer",
    index_rate=0.0
))

print(df1.head(3))
print(df1.tail(3))
```

---

# Scenario 2 — Two Tracks: Spitzer + Equal Principal (aggregate)

```python
trackA = to_df(amortization_schedule(
    amount=500_000,
    annual_rate=0.032,
    months=20*12,
    method="spitzer"
))

trackB = to_df(amortization_schedule(
    amount=300_000,
    annual_rate=0.020,   # Prime assumption as a number here
    months=20*12,
    method="equal"
))

wide2, total2 = combine_tracks({"A_fixed_spitzer": trackA, "B_prime_equal": trackB})

print(total2.head(5))
print(total2.tail(5))
```

---

# Scenario 3 — CPI-linked Spitzer + 24 months interest-only grace

```python
df3 = to_df(amortization_schedule(
    amount=400_000,
    annual_rate=0.024,
    months=25*12,
    method="spitzer",
    index_rate=0.02,           # CPI assumption: 2% yearly
    grace_period=24,
    grace_type="interest_only"
))

print(df3.loc[1:5])
print(df3.loc[23:27])   # show grace ending + payment jump
print(df3.tail(3))
```

---

# Scenario 4 — Variable (one scheduled rate jump) Spitzer

```python
df4 = to_df(amortization_schedule(
    amount=700_000,
    annual_rate=0.030,
    months=30*12,
    method="spitzer",
    rate_change_month=60,      # after 5 years
    rate_change_delta=0.015    # +1.5%
))

print(df4.loc[58:64])   # show the jump window
```

---

# Scenario 5 — Multi-track + multiple events (rate changes + multiple prepays)

The PDF function supports **one** rate change and **one** prepay per track.
For “many events”, the clean way is: **apply the PDF function in segments**.

Here’s a small helper that stitches segments together per track:

```python
def schedule_with_events(
    amount: float,
    months: int,
    method: str,
    annual_rate: float,
    index_rate: float = 0.0,
    grace: Optional[Dict] = None,
    rate_changes: Optional[List[Dict]] = None,   # [{"month": 37, "delta": 0.01}, ...]
    prepays: Optional[List[Dict]] = None         # [{"month": 60, "amount": 50_000, "option":"payment"}, ...]
) -> pd.DataFrame:
    grace = grace or {"period": 0, "type": "none"}
    rate_changes = sorted(rate_changes or [], key=lambda x: x["month"])
    prepays = sorted(prepays or [], key=lambda x: x["month"])

    # Convert multi-event into a unified event list
    events = []
    for rc in rate_changes:
        events.append(("rate", rc["month"], rc))
    for pp in prepays:
        events.append(("prepay", pp["month"], pp))
    events.sort(key=lambda x: x[1])

    rows = []
    current_balance = amount
    current_rate = annual_rate
    start_month = 1

    # We'll run consecutive segments until next event month, applying at most one event per segment end
    for (etype, emonth, payload) in events + [("end", months+1, None)]:
        if emonth < start_month:
            continue

        seg_len = min(emonth - start_month, months - start_month + 1)
        if seg_len <= 0:
            # apply event immediately
            if etype == "rate":
                current_rate += payload["delta"]
            elif etype == "prepay":
                current_balance = max(0.0, current_balance - payload["amount"])
            continue

        # Only apply grace if segment starts within grace window
        g_period = 0
        g_type = "none"
        if start_month == 1 and grace.get("period", 0) > 0:
            g_period = grace["period"]
            g_type = grace["type"]

        # Segment run (no internal events)
        seg_rows = amortization_schedule(
            amount=current_balance,
            annual_rate=current_rate,
            months=seg_len,
            method=method,
            index_rate=index_rate,
            grace_period=g_period,
            grace_type=g_type
        )

        # Re-index months to global month count
        for i, r in enumerate(seg_rows, start=start_month):
            r2 = dict(r)
            r2["Month"] = i
            rows.append(r2)

        # update for next segment
        current_balance = rows[-1]["Balance"]
        start_month += seg_len

        # apply event at boundary
        if etype == "rate":
            current_rate += payload["delta"]
        elif etype == "prepay":
            # apply extra payment at that month by directly reducing balance
            amt = min(payload["amount"], current_balance)
            current_balance -= amt
            # optional: reduce-payment behavior could be done by recomputing payment in next segment;
            # our segment runner will naturally recompute from new balance.

    return to_df(rows)
```

Now define Scenario 5 as you described (tracks + events):

```python
# Track A: Prime-like (Spitzer, multiple rate deltas)
A = schedule_with_events(
    amount=400_000,
    months=25*12,
    method="spitzer",
    annual_rate=0.020,     # "Prime assumption"
    rate_changes=[
        {"month": 37, "delta": 0.010},
        {"month": 85, "delta": 0.005},
    ],
)

# Track B: CPI-linked, Equal Principal, 12m interest-only grace
B = schedule_with_events(
    amount=300_000,
    months=25*12,
    method="equal",
    annual_rate=0.022,
    index_rate=0.02,
    grace={"period": 12, "type": "interest_only"},
)

# Track C: Fixed unlinked, Spitzer, partial prepay at month 60
C = schedule_with_events(
    amount=200_000,
    months=20*12,
    method="spitzer",
    annual_rate=0.038,
    prepays=[{"month": 60, "amount": 50_000, "option": "payment"}],
)

wide5, total5 = combine_tracks({"A_prime": A, "B_cpi_equal": B, "C_fixed": C})

print(total5.loc[55:65])   # around prepay
print(total5.loc[35:40])   # around first rate change
print(total5.tail(5))
```

---

## If you want this to match Mashkantaman even closer

Tell me which exact **track list / naming** you want (Prime, fixed unlinked, fixed linked, variable every 5 linked/unlinked, etc.), and I’ll provide a small enum + config schema so you can define scenarios like:

```python
tracks=[TrackConfig(...), ...]
events=[RateChange(...), Prepay(...), Grace(...)]
```

and get:

* per-track amortization tables
* combined totals
* summary metrics (total interest, max payment, etc.)
