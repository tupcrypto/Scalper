# ============================
# grid_engine.py
# ============================

import math
import config

GRID_LEVELS = config.GRID_LEVELS          # e.g. 14
GRID_RANGE_PCT = config.GRID_RANGE_PCT    # e.g. 0.0065


def check_grid_signal(price, balance):
    """
    Determines whether to BUY, SELL, or HOLD
    based on grid distribution and available balance.
    """

    if price <= 0:
        return "HOLD"

    # total capital allocation
    total_allocation = (balance * config.MAX_CAPITAL_PCT) / 100

    if total_allocation <= 0:
        return "HOLD"

    # split allocation across grid levels
    grid_unit = total_allocation / GRID_LEVELS

    # compute price bands
    upper_px = price * (1 + GRID_RANGE_PCT)
    lower_px = price * (1 - GRID_RANGE_PCT)

    # BUY if price is below lower band
    if price < lower_px:
        return {
            "action": "BUY",
            "amount": grid_unit,
            "reason": f"Price dropped below grid lower band ({lower_px:.4f})"
        }

    # SELL if price is above upper band
    if price > upper_px:
        return {
            "action": "SELL",
            "amount": grid_unit,
            "reason": f"Price exceeded grid upper band ({upper_px:.4f})"
        }

    # HOLD in neutral area
    return {
        "action": "HOLD",
        "amount": 0,
        "reason": "Price inside neutral grid"
    }

