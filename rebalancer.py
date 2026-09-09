"""
rebalancer.py

Reference implementation of the portfolio rebalancing calculation shown in
the "Account ABC" spreadsheet. This is the System Under Test (SUT) for the
manual and automated test suites in this project.

BUSINESS RULE BEING IMPLEMENTED
--------------------------------
For each security in an account:

    target_value  = target_pct  / 100 * total_assets
    current_value = current_pct / 100 * total_assets
    dollar_diff   = target_value - current_value
    variance_pct  = current_pct - target_pct        (matches the sheet's
                                                       "target Variance" column:
                                                       negative = underweight = BUY,
                                                       positive = overweight  = SELL)
    shares_raw    = dollar_diff / unit_price
    shares_rounded = round(shares_raw) to the nearest whole share,
                     sign preserved (standard round-half-up on the magnitude)

    action = "BUY"  if shares_rounded > 0
             "SELL" if shares_rounded < 0
             "HOLD" if shares_rounded == 0

ASSUMPTIONS DOCUMENTED FOR TESTING (confirm with the business/product owner
before treating these as final — they are exactly the kind of ambiguity a
tester should flag rather than silently assume):

1. Fractional shares are NOT tradable. Every result is rounded to a whole
   share using standard round-half-up on the absolute value, then the sign
   (buy vs. sell) is re-applied. E.g. 66.67 -> 67, -45.45 -> -45... wait,
   45.45 rounds to 45 (0.45 rounds down), while 66.67 rounds to 67
   (0.67 rounds up) — see the rounding helper below for the exact rule.
2. total_assets must be strictly positive. Zero or negative total assets is
   treated as invalid input (raises ValueError) rather than silently
   producing 0/0 or infinite share counts.
3. unit_price must be strictly positive for the same reason (avoids a
   ZeroDivisionError / negative-share nonsense from a bad price feed).
4. target_pct and current_pct must be >= 0. Negative percentages are
   rejected as bad data.
5. The engine does NOT require sum(target_pct) == 100 or
   sum(current_pct) == 100 across the account — it computes each security
   independently, exactly as the spreadsheet does. A separate validation
   helper (validate_allocations) is provided so a caller/tester can check
   that invariant explicitly and decide what to do about it.
6. No minimum trade size / no cash-sufficiency check is enforced. A real
   trading system would likely also verify total buys can be funded by
   total sells (or available cash) before submitting orders — this
   reference implementation intentionally leaves that out so tests can
   demonstrate it's a gap (see TC-11 / TC-15 in the manual test cases).
7. VESTING (see TC-25): target_pct/current_pct are applied against the
   VESTED (investable) portion of total_assets, not the full account
   value. investable_base = total_assets * vested_pct / 100. Passing the
   default vested_pct=100.0 reproduces every prior calculation exactly
   (investable_base == total_assets), so this is backward compatible with
   TC-01 through TC-16/19/20. This is a design DECISION made to make
   TC-25 automatable, not a confirmed product requirement — flag it for
   business sign-off before relying on it.
"""

from dataclasses import dataclass, asdict
from typing import List
import math


@dataclass
class SecurityInput:
    symbol: str
    target_pct: float
    current_pct: float
    unit_price: float


@dataclass
class RebalanceResult:
    symbol: str
    target_pct: float
    current_pct: float
    variance_pct: float
    unit_price: float
    dollar_diff: float
    shares_raw: float
    shares_rounded: int
    action: str  # "BUY", "SELL", "HOLD"
    vested_pct: float = 100.0
    investable_base: float = 0.0

    def as_dict(self):
        return asdict(self)


def _round_shares(raw_shares: float) -> int:
    """Round-half-up on magnitude, sign preserved. 0 stays 0."""
    if raw_shares == 0:
        return 0
    sign = 1 if raw_shares > 0 else -1
    return sign * int(math.floor(abs(raw_shares) + 0.5))


def validate_allocations(securities: List[SecurityInput], tolerance: float = 0.01):
    """
    Optional data-integrity check: do target_pct values sum to 100%, and do
    current_pct values sum to 100%? Returns a dict of booleans; does not
    raise, so callers/tests can decide how strict to be.
    """
    target_sum = sum(s.target_pct for s in securities)
    current_sum = sum(s.current_pct for s in securities)
    return {
        "target_sum": target_sum,
        "current_sum": current_sum,
        "target_sums_to_100": abs(target_sum - 100) <= tolerance,
        "current_sums_to_100": abs(current_sum - 100) <= tolerance,
    }


def calculate_rebalance(
    securities: List[SecurityInput], total_assets: float, vested_pct: float = 100.0
) -> List[RebalanceResult]:
    if total_assets is None or total_assets <= 0:
        raise ValueError("total_assets must be a positive number")
    if vested_pct is None or not (0 < vested_pct <= 100):
        raise ValueError("vested_pct must be > 0 and <= 100")

    investable_base = total_assets * vested_pct / 100

    if not securities:
        return []

    results = []
    for sec in securities:
        if sec.unit_price is None or sec.unit_price <= 0:
            raise ValueError(f"{sec.symbol}: unit_price must be a positive number")
        if sec.target_pct < 0 or sec.current_pct < 0:
            raise ValueError(f"{sec.symbol}: percentages cannot be negative")

        target_value = sec.target_pct / 100 * investable_base
        current_value = sec.current_pct / 100 * investable_base
        dollar_diff = target_value - current_value
        variance_pct = sec.current_pct - sec.target_pct
        shares_raw = dollar_diff / sec.unit_price
        shares_rounded = _round_shares(shares_raw)

        if shares_rounded > 0:
            action = "BUY"
        elif shares_rounded < 0:
            action = "SELL"
        else:
            action = "HOLD"

        results.append(
            RebalanceResult(
                symbol=sec.symbol,
                target_pct=sec.target_pct,
                current_pct=sec.current_pct,
                variance_pct=round(variance_pct, 6),
                unit_price=sec.unit_price,
                dollar_diff=round(dollar_diff, 6),
                shares_raw=shares_raw,
                shares_rounded=shares_rounded,
                action=action,
                vested_pct=vested_pct,
                investable_base=round(investable_base, 6),
            )
        )
    return results


def calculate_single_line(
    current_pct: float, target_pct: float, unit_price: float, total_assets: float, vested_pct: float = 100.0
) -> float:
    """Convenience wrapper used by parametrized single-line unit tests."""
    result = calculate_rebalance(
        [SecurityInput(symbol="X", target_pct=target_pct, current_pct=current_pct, unit_price=unit_price)],
        total_assets=total_assets,
        vested_pct=vested_pct,
    )
    return result[0].shares_rounded

# NOTE: an earlier revision of this file included handle_rebalance_request(),
# a request/response-shaped adapter used to automate the API-contract test
# cases (TC-21-24). It was removed by design decision: this application has
# no live, deployed API, and testing a hand-built adapter proves the adapter
# is internally consistent, not that a real API would behave correctly.
# TC-21-24 are intentionally left as manual/Blocked test cases in
# manual_test_cases.xlsx until a real endpoint exists to test against.
