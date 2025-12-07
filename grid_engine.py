import config

# =====================================================
#  GRID STATE
# =====================================================

# Structure:
# GRID_STATE = {
#   "BTC/USDT": {
#       "center": float,
#       "low": float,
#       "high": float,
#       "gap": float,
#       "amount": float,
#       "levels": [
#           {
#               "price": float,
#               "side": "LONG" or "SHORT",
#               "tp": float,
#               "open": bool,
#           },
#           ...
#       ],
#   },
#   ...
# }

GRID_STATE = {}


def init_grid(pair: str, center_price: float, balance_usdt: float):
    """
    Initialize a fresh grid around center_price for this pair.
    """
    from bingx_api import calc_amount_per_level  # local import to avoid circular

    amount = calc_amount_per_level(center_price, balance_usdt)

    half_range = center_price * config.GRID_RANGE_PCT
    low = center_price - half_range
    high = center_price + half_range
    gap = (high - low) / config.GRID_LEVELS

    levels = []

    for i in range(config.GRID_LEVELS):
        level_price = low + i * gap

        # Below center => LONG grid. Above center => SHORT grid.
        if level_price <= center_price:
            side = "LONG"
            tp = level_price + gap  # TP at next level up
        else:
            side = "SHORT"
            tp = level_price - gap  # TP at next level down

        levels.append({
            "price": level_price,
            "side": side,
            "tp": tp,
            "open": False,
        })

    GRID_STATE[pair] = {
        "center": center_price,
        "low": low,
        "high": high,
        "gap": gap,
        "amount": amount,
        "levels": levels,
    }

    print(f"GRID INIT for {pair}: center={center_price}, low={low}, high={high}, gap={gap}, amount={amount}")


def step_pair(pair: str, price: float, balance_usdt: float):
    """
    One step of grid logic for a pair.

    Returns a list of 'events', each event is dict:
       { "action": "open" / "close" / "reset",
         "pair": str,
         "side": "LONG"/"SHORT",   # for open/close
         "amount": float,
         "level_price": float,
         "tp": float,
       }

    The bot will then execute these events via bingx_api and send Telegram messages.
    """
    events = []

    # If no balance or no price, do nothing.
    if price <= 0 or balance_usdt <= 0:
        return events

    # Ensure grid exists
    if pair not in GRID_STATE:
        init_grid(pair, price, balance_usdt)
        # No trades first tick, we just built grid
        return events

    state = GRID_STATE[pair]
    low = state["low"]
    high = state["high"]
    gap = state["gap"]
    amount = state["amount"]
    levels = state["levels"]

    # Safety: if amount is zero (no capital), re-init with latest balance
    if amount <= 0:
        init_grid(pair, price, balance_usdt)
        state = GRID_STATE[pair]
        low = state["low"]
        high = state["high"]
        gap = state["gap"]
        amount = state["amount"]
        levels = state["levels"]

    # =========================
    # 1) BREAKOUT CHECK
    # =========================
    breakout_buffer = gap  # 1 grid step
    if price < low - breakout_buffer or price > high + breakout_buffer:
        # We consider this a breakout. Close all open grid levels and reset.
        for lvl in levels:
            if lvl["open"]:
                events.append({
                    "action": "close",
                    "pair": pair,
                    "side": lvl["side"],
                    "amount": amount,
                    "level_price": lvl["price"],
                    "tp": lvl["tp"],
                })
                lvl["open"] = False

        # Reset grid around new center
        init_grid(pair, price, balance_usdt)
        events.append({
            "action": "reset",
            "pair": pair,
            "side": "",
            "amount": 0.0,
            "level_price": price,
            "tp": 0.0,
        })
        return events

    # =========================
    # 2) MANAGE EACH LEVEL
    # =========================

    for lvl in levels:
        lvl_price = lvl["price"]
        side = lvl["side"]
        tp = lvl["tp"]
        is_open = lvl["open"]

        # OPEN LOGIC
        if not is_open:
            if side == "LONG" and price <= lvl_price:
                # Open a long grid unit
                events.append({
                    "action": "open",
                    "pair": pair,
                    "side": side,
                    "amount": amount,
                    "level_price": lvl_price,
                    "tp": tp,
                })
                lvl["open"] = True

            elif side == "SHORT" and price >= lvl_price:
                # Open a short grid unit
                events.append({
                    "action": "open",
                    "pair": pair,
                    "side": side,
                    "amount": amount,
                    "level_price": lvl_price,
                    "tp": tp,
                })
                lvl["open"] = True

        # CLOSE LOGIC
        else:
            if side == "LONG" and price >= tp:
                events.append({
                    "action": "close",
                    "pair": pair,
                    "side": side,
                    "amount": amount,
                    "level_price": lvl_price,
                    "tp": tp,
                })
                lvl["open"] = False

            elif side == "SHORT" and price <= tp:
                events.append({
                    "action": "close",
                    "pair": pair,
                    "side": side,
                    "amount": amount,
                    "level_price": lvl_price,
                    "tp": tp,
                })
                lvl["open"] = False

    return events
