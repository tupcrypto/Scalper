import ccxt
import scanner

def get_scalp_signal(pair="BTC/USDT"):
    range_info = scanner.detect_range(pair)
    if not range_info:
        return None

    try:
        exchange = ccxt.Exchange({'id': 'bingx'})
        ticker = exchange.fetch_ticker(pair)
        price = float(ticker["last"])
    except Exception as e:
        print("PRICE ERROR:", e)
        return None

    low = range_info["low"]
    high = range_info["high"]
    atr = range_info["atr"]

    width = high - low
    lower_zone = low + width * 0.15
    upper_zone = high - width * 0.15

    if price <= lower_zone:
        side = "LONG"
        entry = price
        tp = entry * 1.003
        sl = low - atr * 1.2
        reason = "Bounce scalp from range support"
    elif price >= upper_zone:
        side = "SHORT"
        entry = price
        tp = entry * 0.997
        sl = high + atr * 1.2
        reason = "Fade scalp from range resistance"
    else:
        # MID RANGE — do nothing
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
