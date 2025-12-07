import ccxt
import scanner


# =====================================================
#  AGGRESSIVE SCALP / GRID-STYLE SIGNAL GENERATOR
# =====================================================

def get_scalp_signal(pair: str = "BTC/USDT"):
    """
    Aggressive version:
      - Uses 5m ATR band from scanner
      - Considers outer 45% of the band as 'edge zones'
      - Much more likely to take trades
    Still:
      - Mean-reversion idea (buy lower band, short upper band)
      - Uses SL beyond band, small TP
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

    # Aggressive zones: outer 45% of band
    # Inner 10% is "no-man's land", everything else is tradable
    lower_zone = low + width * 0.45
    upper_zone = high - width * 0.45

    side = None
    entry = price
    tp = None
    sl = None
    reason = ""

    # LOWER HALF → LONG BIASED
    if price <= lower_zone:
        side = "LONG"
        # Slightly bigger TP because band is narrower
        tp = entry * 1.004   # ~0.4% up
        sl = low - atr * 1.2
        reason = "Aggressive long: price in lower band zone (mean reversion)."

    # UPPER HALF → SHORT BIASED
    elif price >= upper_zone:
        side = "SHORT"
        tp = entry * 0.996   # ~0.4% down
        sl = high + atr * 1.2
        reason = "Aggressive short: price in upper band zone (mean reversion)."

    else:
        # In a very narrow mid area; skip to avoid pointless chop
        print(f"{pair} in mid band, skipping for now.")
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
