import ccxt
import pandas as pd
import numpy as np
import time

# ======================================
# ATR CALCULATION
# ======================================

def calc_atr(df, period=14):
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    atr = df['TR'].rolling(period).mean().iloc[-1]
    return atr


# ======================================
# RANGE DETECTION
# ======================================

async def detect_range(pair="BTC/USDT"):
    exchange = ccxt.bingx()

    try:
        ohlcv = exchange.fetch_ohlcv(pair, timeframe="15m", limit=50)
    except Exception as e:
        print("DATA ERROR:", e)
        return None

    df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])

    atr = calc_atr(df, 14)

    last_price = df['close'].iloc[-1]

    # MICRO-RANGE DYNAMIC
    grid_low  = last_price - atr * 1.5
    grid_high = last_price + atr * 1.5

    # LIQUIDITY FILTER
    vol = df['vol'].iloc[-1]
    avg_vol = df['vol'].mean()

    if vol < avg_vol * 0.5:
        return None  # avoid dead zones

    return {
        "low": grid_low,
        "high": grid_high,
        "atr": atr,
        "price": last_price,
        "timestamp": time.time()
    }
