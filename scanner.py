import ccxt
import pandas as pd
import time

# =====================================================
# ATR CALCULATION
# =====================================================

def calc_atr(df, period: int = 14) -> float:
    """
    Classic ATR calculation on a pandas OHLCV DataFrame.
    """
    if df.empty or len(df) < period + 2:
        return 0.0

    df = df.copy()
    df["H-L"] = df["high"] - df["low"]
    df["H-PC"] = (df["high"] - df["close"].shift(1)).abs()
    df["L-PC"] = (df["low"] - df["close"].shift(1)).abs()
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
    atr = df["TR"].rolling(period).mean().iloc[-1]
    return float(atr)


# =====================================================
# RANGE DETECTION
# =====================================================

def detect_range(pair: str = "BTC/USDT"):
    """
    Fetch 15m OHLCV, compute ATR and return a micro-range for scalping.
    Returns dict with keys: low, high, atr, price, timestamp
    or None if market not suitable (low liquidity / no data).
    """
    exchange = ccxt.bingx()

    try:
        ohlcv = exchange.fetch_ohlcv(pair, timeframe="15m", limit=60)
    except Exception as e:
        print("DATA ERROR in detect_range:", e)
        return None

    if not ohlcv or len(ohlcv) < 20:
        return None

    df = pd.DataFrame(
        ohlcv,
        columns=["time", "open", "high", "low", "close", "vol"]
    )

    atr = calc_atr(df, 14)
    if atr <= 0:
        return None

    last_price = float(df["close"].iloc[-1])

    # Micro-range: ±1.5 * ATR around current price
    grid_low = last_price - atr * 1.5
    grid_high = last_price + atr * 1.5

    # Liquidity / activity filter
    last_vol = float(df["vol"].iloc[-1])
    avg_vol = float(df["vol"].mean())

    if avg_vol == 0 or last_vol < avg_vol * 0.5:
        # Too dead / illiquid right now
        return None

    return {
        "low": grid_low,
        "high": grid_high,
        "atr": atr,
        "price": last_price,
        "timestamp": time.time(),
    }
