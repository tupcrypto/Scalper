import ccxt
import math
import scanner
import time

# =====================================================
# SCALP SIGNAL GENERATOR (NO REAL ORDERS)
# =====================================================

def get_scalp_signal(pair: str = "BTC/USDT"):
    """
    Uses scanner.detect_range to find a scalping range on BTC/USDT,
    then decides if a LONG or SHORT scalp is attractive near the edges.
    Returns dict with:
        side: 'LONG' or 'SHORT'
        entry: float
        sl: float
        tp: float
        rr: float (approx risk:reward)
        price: current price
        range_low, range_high, atr, reason, timestamp
    or None if no good setup right now.
    """

    range_info = scanner.detect_range(pair)
    if not range_info:
        return None

    low = range_info["low"]
    high = range_info["high"]
    atr = range_info["atr"]

    width = high - low
    if width <= 0:
        return None

    # Get current price from BingX
    exchange = ccxt.bingx()
    try:
        ticker = exchange.fetch_ticker(pair)
        price = float(ticker["last"])
    except Exception as e:
        print("TICKER ERROR in get_scalp_signal:", e)
        return None

    # Define zones
    lower_zone = low + width * 0.15
    upper_zone = high - width * 0.15

    side = None
    entry = price
    sl = None
    tp = None
    reason = ""

    # If price is close to bottom of range -> long scalp
    if price <= lower_zone:
        side = "LONG"
        # Small TP ~0.3% above entry
        tp = entry * 1.003
        # SL a bit below range low
        sl = low - atr * 1.2
        reason = "Price near range support with decent volatility."

    # If price is close to top of range -> short scalp
    elif price >= upper_zone:
        side = "SHORT"
        # Small TP ~0.3% below entry
        tp = entry * 0.997
        # SL a bit above range high
        sl = high + atr * 1.2
        reason = "Price near range resistance with decent volatility."

    else:
        # In the middle of the range, not a good edge to scalp
        return None

    # Approx risk:reward
    rr = None
    if side == "LONG" and sl < entry and tp > entry:
        risk = entry - sl
        reward = tp - entry
        rr = reward / risk if risk > 0 else None
    elif side == "SHORT" and sl > entry and tp < entry:
        risk = sl - entry
        reward = entry - tp
        rr = reward / risk if risk > 0 else None

    return {
        "side": side,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "rr": rr,
        "price": price,
        "range_low": low,
        "range_high": high,
        "atr": atr,
        "reason": reason,
        "timestamp": time.time(),
        "pair": pair,
    }
