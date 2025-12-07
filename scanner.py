import ccxt
import pandas as pd

# =====================================================
# ATR
# =====================================================

def calc_atr(df, period: int = 14) -> float:
    df = df.copy()
    df["H-L"] = df["high"] - df["low"]
    df["H-PC"] = (df["high"] - df["close"].shift(1)).abs()
    df["L-PC"] = (df["low"] - df["close"].shift(1)).abs()
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
    atr = df["TR"].rolling(period).mean().iloc[-1]
    return float(atr)


# =====================================================
# RANGE DETECTION (AGGRESSIVE)
# =====================================================

def detect_range(pair: str = "BTC/USDT"):
    """
    Aggressive range detector:
    - Uses 5m candles for responsiveness
    - ATR * 1.5 band (not too wide)
    - Very soft liquidity filter
    - NO trend filter (we let grid logic + SL handle it)
    """
    try:
        exchange = ccxt.bingx()
    except Exception as e:
        print("EXCHANGE INIT ERROR:", e)
        return None

    try:
        ohlcv = exchange.fetch_ohlcv(pair, timeframe="5m", limit=80)
    except Exception as e:
        print("DATA ERROR:", e)
        return None

    if not ohlcv or len(ohlcv) < 30:
        print(f"NOT ENOUGH DATA for {pair}")
        return None

    df = pd.DataFrame(
        ohlcv,
        columns=["time", "open", "high", "low", "close", "vol"]
    )

    atr = calc_atr(df, 14)
    if atr <= 0:
        print(f"BAD ATR for {pair}")
        return None

    last_price = float(df["close"].iloc[-1])

    # Band: ±1.5 * ATR around current price (tighter than before -> more trades)
    grid_low = last_price - atr * 1.5
    grid_high = last_price + atr * 1.5

    # Very soft liquidity filter: only reject totally dead candles
    last_vol = float(df["vol"].iloc[-1])
    avg_vol = float(df["vol"].mean())
    if avg_vol > 0 and last_vol < avg_vol * 0.2:
        print(f"VERY LOW LIQUIDITY on {pair}")
        return None

    return {
        "low": grid_low,
        "high": grid_high,
        "atr": atr,
        "price": last_price,
    }

