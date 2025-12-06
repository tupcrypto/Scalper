import ccxt
import scanner


# =====================================================
#  SCALP SIGNAL GENERATOR (SIGNAL ONLY)
# =====================================================

def get_scalp_signal(pair: str = "BTC/USDT"):
    """
    Use scanner.detect_range to find a scalping range on BTC/USDT,
    then decide LONG/SHORT scalp near the edges.
    Returns dict with fields:
        side, entry, tp, sl, low, high, price, atr, reason
    or None if no good setup now.
    """
    range_info = scanner.detect_range(pair)
    if not range_info:
        print("NO RANGE INFO")
        return None

    low = range_info["low"]
    high = range_info["high"]
    atr = range_info["atr"]

    try:
        exchange = ccxt.bingx()
        ticker = exchange.fetch_ticker(pair)
        price = float(ticker["last"])
    except Exception as e:
        print("PRICE ERROR:", e)
        return None

    width = high - low
    if width <= 0:
        print("BAD WIDTH")
        return None

    lower_zone = low + width * 0.15
    upper_zone = high - width * 0.15

    side = None
    entry = price
    tp = None
    sl = None
    reason = ""

    if price <= lower_zone:
        side = "LONG"
        tp = entry * 1.003   # ~0.3% up
        sl = low - atr * 1.2
        reason = "Price near range support (bounce scalp)."

    elif price >= upper_zone:
        side = "SHORT"
        tp = entry * 0.997   # ~0.3% down
        sl = high + atr * 1.2
        reason = "Price near range resistance (fade scalp)."

    else:
        print("PRICE MID RANGE, NO EDGE")
        return None

    return {
        "side": side,
        "entry": entry,
        "tp": tp,
        "sl": sl,
        "low": low,
        "high": high,
        "price": price,
        "atr": atr,
        "reason": reason,
    }
