# Account ABC — Portfolio Rebalancing Calculation: Testing Assumptions

These assumptions underpin **both** the manual test case sheet
(`manual_test_cases.xlsx`) and the automated test suite
(`Account_ABC_Rebalance_Automated_Tests.ipynb`). They are drawn from the
reference implementation (`rebalancer.py`) and from scope questions raised
during test design. If any assumption below changes, both the manual
sheet's expected results and the automated suite's assertions need to be
updated together as they are not independent.

**System under test:** the "number of shares to buy/sell" calculation --->
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
   This is the single most consequential assumption in the project. Every
   expected value in both suites depends on this rule being correct.
 
2. **variance% = current% − target%**, matching the original spreadsheet's
   "target Variance" column convention: negative = underweight = BUY,
   positive = overweight = SELL.
   
3. **The dollar amount to trade** is variance% × investable_base, converted
   to shares by dividing by unit_price. No spread, slippage, or fee
   adjusts this figure.

## Input validation assumptions

4. **total_assets must be strictly positive.** Zero or negative is invalid
   input (raises an error), not a valid 0/0 or infinite result.
  
5. **unit_price must be strictly positive**, guarding against a bad price
   feed producing a divide-by-zero or nonsense negative-share result.
 
6. **target%/current% must be ≥ 0.** Negative percentages are rejected as
   bad data.
   
8. **Percentages are NOT required to sum to 100%** across the account. The
   engine computes each security independently, exactly as the spreadsheet
   does, rather than validating the whole allocation as a set.
  

## Scope assumptions — intentionally out of scope

8. **No cash-sufficiency / self-funding check.** The calculation does not
   verify that total buys can be funded by total sells (or available cash)
   before recommending trades. A real trading system likely would.

9. **No transaction costs, commissions, bid/ask spread, or tax impact**
   (e.g. capital gains) factor into the share calculation. unit_price is a
   single point-in-time number, not a live quote with a spread.
   
11. **Vesting: target%/current% apply against the *vested* portion of
    total_assets, not the full account value** —
    `investable_base = total_assets * vested_pct / 100`. `vested_pct`
    defaults to 100, so every pre-vesting test case is unaffected.
    
    **This is a design decision made to make TC-25 automatable, the original problem statement only
    ever said "100% is vested," so applying target% to a *reduced* base
    when vesting is partial is our interpretation/assumptions.
    
  
13. **Single account, single currency.** No cross-account cash sharing, no
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
    idempotency) are manual-only, Status = Blocked. 
