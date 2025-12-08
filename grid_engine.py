# ============================
# grid_engine.py  (FULL FILE)
# ============================

import config

def check_grid_signal(price: float, balance: float):
    """
    Simple grid logic:
    - Use MAX_CAPITAL_PCT of futures balance
    - Split into GRID_LEVELS
    - If price < lower band -> BUY
    - If price > upper band -> SELL
    - Else HOLD
    Returns dict with action, amount (position size), reason.
    """

    price = float(price)
    balance = float(balance)

    if price <= 0:
        return {
            "action": "HOLD",
            "amount": 0.0,
            "reason": "Invalid price"
        }

    if balance <= 0:
        return {
            "action": "HOLD",
            "amount": 0.0,
            "reason": "No futures balance"
        }

    total_alloc = balance * (config.MAX_CAPITAL_PCT / 100.0)
    if total_alloc <= 0:
        return {
            "action": "HOLD",
            "amount": 0.0,
            "reason": "No capital allocation"
        }

    # capital per grid step in USDT
    grid_capital = total_alloc / float(config.GRID_LEVELS)

    # convert capital to contracts/coins
    qty_per_step = grid_capital / price

    upper_band = price * (1.0 + config.GRID_RANGE_PCT)
    lower_band = price * (1.0 - config.GRID_RANGE_PCT)

    # BUY if below lower band
    if price < lower_band:
        return {
            "action": "BUY",
            "amount": float(qty_per_step),
            "reason": f"Price {price:.4f} < lower band {lower_band:.4f}"
        }

    # SELL if above upper band
    if price > upper_band:
        return {
            "action": "SELL",
            "amount": float(qty_per_step),
            "reason": f"Price {price:.4f} > upper band {upper_band:.4f}"
        }

    # Otherwise HOLD
    return {
        "action": "HOLD",
        "amount": 0.0,
        "reason": "Neutral zone"
    }
