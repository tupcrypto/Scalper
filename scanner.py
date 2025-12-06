import ccxt
import pandas as pd

def calc_atr(df, period: int = 14):
    df = df.copy()
    df["H-L"] = df["high"] - df["low"]
    df["H-PC"] = (df["high"] - df["close"].shift(1)).abs()
    df["L-PC"] = (df["low"] - df["close"].shift(1)).abs()
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
    atr = df["TR"].rolling(period).mean().iloc[-1]
    return float(atr)

def detect_range(pair="BTC/USDT"):
    try:
        exchange = ccxt.Exchange({'id': 'bingx'})
    except Exception as e:
        print("EXCHANGE INIT ERROR:", e)
        return None

    try:
        ohlcv = exchange.fetch_ohlcv(pair, timeframe="15m", limit=50)
    except Exception as e:
        print("DATA ERROR:", e)
        return None

    if not ohlcv:
        return None

    df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','vol'])
    atr = calc_atr(df, 14)
    last_price = float(df['close'].iloc[-1])

    grid_low = last_price - atr * 1.5
    grid_high = last_price + atr * 1.5

    last_vol = float(df['vol'].iloc[-1])
    avg_vol = float(df['vol'].mean())

    if last_vol < avg_vol * 0.6:
        print("LOW LIQUIDITY")
        return None

    return {
        "low": grid_low,
        "high": grid_high,
        "atr": atr,
        "price": last_price,
    }
