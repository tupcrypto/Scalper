# ============================
# grid_engine.py
# ============================

import config

GRID_LEVELS = config.GRID_LEVELS
GRID_RANGE_PCT = config.GRID_RANGE_PCT


def check_grid_signal(price, balance):
    if price <= 0 or balance <= 0:
        return {
            "action": "HOLD",
            "amount": 0,
            "reason": "No balance or invalid price"
        }

    total_allocation = (float(balance) * float(config.MAX_CAPITAL_PCT)) / 100

    if total_allocation <= 0:
        return {
            "action": "HOLD",
            "amount": 0,
            "reason": "No allocation"
        }

    grid_unit = float(total_allocation) / float(GRID_LEVELS)

    upper_px = float(price) * (1 + float(GRID_RANGE_PCT))
    lower_px = float(price) * (1 - float(GRID_RANGE_PCT))

    if float(price) < lower_px:
        return {
            "action": "BUY",
            "amount": float(grid_unit),
            "reason": f"Below grid lower band ({lower_px:.4f})"
        }

    if float(price) > upper_px:
        return {
            "action": "SELL",
            "amount": float(grid_unit),
            "reason": f"Above grid upper band ({upper_px:.4f})"
        }

    return {
        "action": "HOLD",
        "amount": 0,
        "reason": "Neutral zone"
    }

