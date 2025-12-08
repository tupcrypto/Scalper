import config
import bitget_api
import math

# ============================================================
# AGGRESSIVE MULTI-LEVEL GRID
# ============================================================

def get_grid_levels(price):
    """
    Build 10 micro-grid levels:
    5 above and 5 below price
    """
    rng = config.GRID_RANGE_PCT  # example: 0.0065
    center = price

    levels = []
    for i in range(1, 6):  # 5 up, 5 down
        up = center * (1 + rng * i)
        dn = center * (1 - rng * i)
        levels.append(up)
        levels.append(dn)

    return sorted(levels)


def check_grid_signal(pair, price, balance):
    """
    Determine if price is outside nearest grid level
    """

    levels = get_grid_levels(price)
    lower_levels = [lvl for lvl in levels if lvl < price]
    upper_levels = [lvl for lvl in levels if lvl > price]

    if not lower_levels or not upper_levels:
        return "No grid actions"

    nearest_lower = max(lower_levels)
    nearest_upper = min(upper_levels)

    # mean reversion trigger:
    if price < nearest_lower:
        return f"BUY {pair} — price {price} < grid {nearest_lower}"

    if price > nearest_upper:
        return f"SELL {pair} — price {price} > grid {nearest_upper}"

    return "No grid actions"


# ============================================================
# LIVE EXECUTION
# ============================================================

def execute_if_needed(pair, price, balance):

    if not config.LIVE_TRADING:
        return "Simulation only"

    signal = check_grid_signal(pair, price, balance)

    if "BUY" in signal:
        place_buy(pair, price, balance)

    elif "SELL" in signal:
        place_sell(pair, price, balance)


def place_buy(pair, price, balance):
    """
    Aggressive BUY scalp:
    - position size: balance × capital %
    - SL: -0.35%
    - TP: +0.35%
    """

    allocation = balance * (config.MAX_CAPITAL_PCT / 100)
    qty = allocation / price

    ex = bitget_api.get_exchange()

    try:
        order = ex.create_order(
            symbol=pair,
            type="market",
            side="buy",
            amount=qty,
        )

        print(f"[LIVE BUY] {pair} qty={qty} @ {price}")

        # SL/TP levels
        sl = price * 0.9965
        tp = price * 1.0035

        ex.create_order(
            symbol=pair,
            type="stop_market",
            side="sell",
            stopPrice=sl,
        )

        ex.create_order(
            symbol=pair,
            type="take_profit_market",
            side="sell",
            stopPrice=tp,
        )

    except Exception as e:
        print(f"[LIVE BUY ERROR] {str(e)}")


def place_sell(pair, price, balance):
    """
    Aggressive SELL scalp:
    - position size: balance × capital %
    - SL: +0.35%
    - TP: -0.35%
    """

    allocation = balance * (config.MAX_CAPITAL_PCT / 100)
    qty = allocation / price

    ex = bitget_api.get_exchange()

    try:
        order = ex.create_order(
            symbol=pair,
            type="market",
            side="sell",
            amount=qty,
        )

        print(f"[LIVE SELL] {pair} qty={qty} @ {price}")

        sl = price * 1.0035
        tp = price * 0.9965

        ex.create_order(
            symbol=pair,
            type="stop_market",
            side="buy",
            stopPrice=sl,
        )

        ex.create_order(
            symbol=pair,
            type="take_profit_market",
            side="buy",
            stopPrice=tp,
        )

    except Exception as e:
        print(f"[LIVE SELL ERROR] {str(e)}")

