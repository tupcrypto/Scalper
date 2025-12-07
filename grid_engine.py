import ccxt
import scanner


# =====================================================
#  SCALP / GRID-STYLE SIGNAL GENERATOR
# =====================================================

def get_scalp_signal(pair: str = "BTC/USDT"):
    """
    Use scanner.detect_range to find a scalping range on a pair,
    then decide LONG/SHORT scalp near the edges.

    Now more aggressive:
      - 5m timeframe
      - wider ATR band
      - uses outer 30% as 'grid' zones (faster entries)
    """
    range_info = scanner.detect_range(pair)
    if not range_info:
        print(f"NO RANGE INFO for {pair}")
        return None

    low = range_info["low"]
    high = range_info["high"]
    atr = range_info["atr"]

    try:
        exchange = ccxt.bingx()
        ticker = exchange.fetch_ticker(pair)
        price = float(ticker["last"])
    except Exception as e:
        print(f"PRICE ERROR for {pair}:", e)
        return None

    width = high - low
    if width <= 0:
        print(f"BAD WIDTH for {pair}")
        return None

    # More aggressive zones: outer 30% instead of 15%
    lower_zone = low + width * 0.3
    upper_zone = high - width * 0.3

    side = None
    entry = price
    tp = None
    sl = None
    reason = ""

    if price <= lower_zone:
        side = "LONG"
        tp = entry * 1.0035   # ~0.35% up
        sl = low - atr * 1.3
        reason = "Price in lower grid zone (mean-reversion long)."

    elif price >= upper_zone:
        side = "SHORT"
        tp = entry * 0.9965   # ~0.35% down
        sl = high + atr * 1.3
        reason = "Price in upper grid zone (mean-reversion short)."

    else:
        # mid-range, no edge
        print(f"{pair} MID RANGE, NO EDGE")
        return None

    return {
        "pair": pair,
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
