# Account ABC — Portfolio Rebalancing Calculation: Testing Assumptions

These assumptions underpin **both** the manual test case sheet
(`manual_test_cases.xlsx`) and the automated test suite
(`Account_ABC_Rebalance_Automated_Tests.ipynb`). They are drawn from the
reference implementation (`rebalancer.py`) and from scope questions raised
during test design. If any assumption below changes, both the manual
sheet's expected results and the automated suite's assertions need to be
updated together — they are not independent.

**System under test:** the "number of shares to buy/sell" calculation —
given each security's target%, current%, and unit price, and the account's
total assets, compute the exact trade needed to bring every position back
to its target allocation.

```
target_value   = target_pct  / 100 * investable_base
current_value  = current_pct / 100 * investable_base
dollar_diff    = target_value - current_value
variance_pct   = current_pct - target_pct   (negative = underweight = BUY,
                                              positive = overweight  = SELL)
shares_raw     = dollar_diff / unit_price
shares_rounded = round shares_raw to the nearest whole share (sign preserved)
action         = BUY if shares_rounded > 0, SELL if < 0, HOLD if == 0

investable_base = total_assets * vested_pct / 100   (vested_pct defaults to 100)
```

---

## Core calculation assumptions

1. **Fractional shares are not tradable.** Every result rounds to a whole
   share using standard round-half-up on the magnitude, sign preserved
   (66.667 → 67 rounds up; −45.4545 → −45 rounds down, since 0.4545 < 0.5).
   This is the single most consequential assumption in the project — every
   expected value in both suites depends on this rule being correct.
   *Covered by: TC-01, TC-10, TC-16.*
2. **variance% = current% − target%**, matching the original spreadsheet's
   "target Variance" column convention: negative = underweight = BUY,
   positive = overweight = SELL.
3. **The dollar amount to trade** is variance% × investable_base, converted
   to shares by dividing by unit_price. No spread, slippage, or fee
   adjusts this figure.

## Input validation assumptions

4. **total_assets must be strictly positive.** Zero or negative is invalid
   input (raises an error), not a valid 0/0 or infinite result.
   *Covered by: TC-04.*
5. **unit_price must be strictly positive**, guarding against a bad price
   feed producing a divide-by-zero or nonsense negative-share result.
   *Covered by: TC-05, TC-06.*
6. **target%/current% must be ≥ 0.** Negative percentages are rejected as
   bad data. *Covered by: TC-12.*
7. **Percentages are NOT required to sum to 100%** across the account. The
   engine computes each security independently, exactly as the spreadsheet
   does, rather than validating the whole allocation as a set.
   *Covered by: TC-07, TC-08.*

## Scope assumptions — intentionally out of scope, or resolved as a design decision

8. **No cash-sufficiency / self-funding check.** The calculation does not
   verify that total buys can be funded by total sells (or available cash)
   before recommending trades. A real trading system likely would.
   *Demonstrated by: TC-11, TC-15 (documented gap, not silently assumed away).*
9. **No transaction costs, commissions, bid/ask spread, or tax impact**
   (e.g. capital gains) factor into the share calculation. unit_price is a
   single point-in-time number, not a live quote with a spread.
10. **Vesting: target%/current% apply against the *vested* portion of
    total_assets, not the full account value** —
    `investable_base = total_assets * vested_pct / 100`. `vested_pct`
    defaults to 100, so every pre-vesting test case is unaffected.
    **This is a design decision made to make TC-25 automatable, not a
    confirmed product requirement** — the original problem statement only
    ever said "100% is vested," so applying target% to a *reduced* base
    when vesting is partial is our interpretation, not something the
    business has signed off on. Confirm before relying on it.
    *Covered by: TC-25 (now automated — see the notebook's Section 2).*
11. **Single account, single currency.** No cross-account cash sharing, no
    multi-currency conversion.

## Interface/environment assumptions

12. **total_assets is a live snapshot, not a fixed target.** It is whatever
    the account happens to be worth right now (the denominator for every
    percentage), and it is expected to change daily from ordinary price
    movement — nothing in the system holds it constant.
13. **No live UI exists in this reference project.** TC-17/TC-18 remain
    manual-only for that reason — both are genuinely about a human looking
    at a screen (display formatting, an interactive re-run workflow),
    which isn't meaningfully unit-testable the way calculation logic is.
14. **No live, deployed API exists in this reference project.** TC-21
    through TC-24 (schema, error handling, malformed requests,
    idempotency) are manual-only, Status = Blocked. An earlier revision
    briefly automated these against a hand-built request/response adapter
    — the same technique used to unit-test a Flask view function or a
    Lambda handler without deploying it — but this was deliberately
    reverted: a test that calls a mock built solely to be tested proves
    the mock is internally consistent, not that a real API would behave
    correctly. That's a different, weaker kind of confidence than TC-25's
    vesting automation, which tests this system's own (extended) business
    rule rather than a stand-in for an interface that doesn't exist.
    Automate TC-21–TC-24 for real once a deployed endpoint exists.

---

## How the three deliverables relate

| File | Purpose |
|---|---|
| `ASSUMPTIONS.md` (this file) | The shared source of truth both suites are built against |
| `manual_test_cases.xlsx` | 25 test cases: calculation logic, input validation, vesting, API contract, and the UI layer |
| `Account_ABC_Rebalance_Automated_Tests.ipynb` | 28 automated `pytest` tests (via `ipytest`) covering 19 of the 25 manual cases; executed end-to-end and verified passing before delivery |

Manual and automated coverage are **not** 1:1 by design — **6 of the 25
manual cases are intentionally manual-only**: TC-17/TC-18 because they're
fundamentally about a human looking at a screen, and TC-21–TC-24 (API
contract) because this project has no live API to test against. TC-21–24
were briefly automated against a hand-built adapter and then deliberately
reverted (see assumption #14) — a green test there would have proven the
adapter self-consistent, not that a real deployed API behaves correctly,
which is a materially weaker and slightly misleading kind of confidence.
TC-25 (vesting) stayed automated by contrast, because it tests this
system's own extended business rule, clearly flagged as needing sign-off,
rather than a stand-in for an interface that doesn't exist.
