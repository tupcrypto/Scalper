import ccxt
import asyncio
from config import *

exchange = ccxt.bybit({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True,
    "options": {
        "defaultType": "swap"
    }
})

async def get_balance():
    bal = await exchange.fetch_balance()
    return float(bal["USDT"]["free"])

async def get_price(symbol):
    ticker = await exchange.fetch_ticker(symbol)
    return float(ticker["last"])

async def set_leverage(symbol):
    try:
        await exchange.set_leverage(LEVERAGE, symbol)
    except:
        pass

async def place_order(symbol, side, price):
    qty = round(ORDER_USDT / price, 6)
    params = {"reduceOnly": False}
    return await exchange.create_order(
        symbol=symbol,
        type="market",
        side=side,
        amount=qty,
        params=params
    )

async def grid_step(symbol):
    await set_leverage(symbol)

    price = await get_price(symbol)
    buy_price = price * (1 - GRID_GAP_PCT)
    sell_price = price * (1 + GRID_GAP_PCT)

    await place_order(symbol, "buy", buy_price)
    await place_order(symbol, "sell", sell_price)

async def close():
    await exchange.close()
