import ccxt
import pandas as pd

# =====================================================
# ATR & TREND
# =====================================================

def calc_atr(df, period: int = 14) -> float:
    df = df.copy()
    df["H-L"] = df["high"] - df["low"]
    df["H-PC"] = (df["high"] - df["close"].shift(1)).abs()
    df["L-PC"] = (df["low"] - df["close"].shift(1)).abs()
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
    atr = df["TR"].rolling(period).mean().iloc[-1]
    return float(atr)


def calc_trend_strength(df) -> float:
    """
    Very simple trend measure: EMA slope normalized by price.
    Higher absolute value => stronger trend / breakout.
    """
    df = df.copy()
    df["ema"] = df["close"].ewm(span=50).mean()
    # slope over last 5 candles
    slope = df["ema"].iloc[-1] - df["ema"].iloc[-6]
    price = df["close"].iloc[-1]
    if price <= 0:
        return 0.0
    return float(slope / price)


# =====================================================
# RANGE DETECTION
# =====================================================

def detect_range(pair: str = "BTC/USDT"):
    """
    Fetch 5m OHLCV, compute ATR and a micro-range for scalping.
    Returns dict {low, high, atr, price, trend_strength} or None.
    """
    try:
        exchange = ccxt.bingx()
    except Exception as e:
        print("EXCHANGE INIT ERROR:", e)
        return None

    try:
        # 5m timeframe for more responsive, more trades
        ohlcv = exchange.fetch_ohlcv(pair, timeframe="5m", limit=80)
    except Exception as e:
        print("DATA ERROR:", e)
        return None

    if not ohlcv or len(ohlcv) < 30:
        print("NOT ENOUGH DATA")
        return None

    df = pd.DataFrame(
        ohlcv,
        columns=["time", "open", "high", "low", "close", "vol"]
    )

    atr = calc_atr(df, 14)
    if atr <= 0:
        print("BAD ATR")
        return None

    last_price = float(df["close"].iloc[-1])

    # Range: ±2 * ATR around current price (wider, more trades)
    grid_low = last_price - atr * 2.0
    grid_high = last_price + atr * 2.0

    # Liquidity filter
    last_vol = float(df["vol"].iloc[-1])
    avg_vol = float(df["vol"].mean())
    if avg_vol == 0 or last_vol < avg_vol * 0.4:
        print(f"LOW LIQUIDITY on {pair}")
        return None

    # Trend filter (avoid strong breakouts)
    trend_strength = calc_trend_strength(df)
    # If EMA slope is very strong, we consider it breakout/trend and skip
    if abs(trend_strength) > 0.01:  # tweakable
        print(f"STRONG TREND on {pair}, skipping range trade.")
        return None

    return {
        "low": grid_low,
        "high": grid_high,
        "atr": atr,
        "price": last_price,
        "trend_strength": trend_strength,
    }
