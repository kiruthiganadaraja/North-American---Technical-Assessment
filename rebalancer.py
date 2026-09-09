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
