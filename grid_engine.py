# grid_engine.py

import ccxt.async_support as ccxt
from decimal import Decimal
import config
import asyncio

# -------------------------
#  Load Correct Exchange
# -------------------------
async def get_exchange():
    ex = ccxt.blofin({
        "apiKey": config.EXCHANGE_API_KEY,
        "secret": config.EXCHANGE_API_SECRET,
        "password": config.EXCHANGE_API_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",
            "createMarketBuyOrderRequiresPrice": False
        }
    })
    await ex.load_markets()
    return ex


# -------------------------
#  Fetch futures balance
# -------------------------
async def get_futures_balance(exchange):
    try:
        bal = await exchange.fetch_balance()
        if "USDT" in bal:
            total = bal["USDT"]["total"]
            if total:
                return Decimal(str(total))
        return Decimal("0")
    except Exception as e:
        return Decimal("0")


# -------------------------
#  Fetch price
# -------------------------
async def get_price(exchange, symbol):
    try:
        t = await exchange.fetch_ticker(symbol)
        return Decimal(str(t["last"]))
    except:
        return None


# -------------------------
#  Execute order
# -------------------------
async def execute_order(exchange, symbol, side, usdt_amount):
    """
    BloFin futures only need qty, NOT cost.
    We convert USDT → contract size by price.
    """

    price = await get_price(exchange, symbol)
    if price is None:
        return False, "Price unavailable"

    qty = (Decimal(usdt_amount) / price).quantize(Decimal("0.0001"))

    try:
        order = await exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=float(qty),
        )
        return True, str(order)

    except Exception as e:
        return False, str(e)


# -------------------------
#  Main grid logic per pair
# -------------------------
async def run_grid(exchange, symbol, balance):
    price = await get_price(exchange, symbol)

    if price is None:
        return f"[GRID] {symbol} — price N/A"

    # neutral mode = simple Pionex style
    # grid band: +/- 0.5%
    upper = price * Decimal("1.005")
    lower = price * Decimal("0.995")

    if balance < config.MIN_ORDER:
        return f"[GRID] {symbol} — NO ORDER (Balance too small)"

    mid = (upper + lower) / 2

    if price < lower:
        # LONG ENTRY
        success, msg = await execute_order(exchange, symbol, "buy", config.MIN_ORDER)
        return f"[GRID] {symbol} — LONG @ {price} → {msg}"

    elif price > upper:
        # SHORT ENTRY
        success, msg = await execute_order(exchange, symbol, "sell", config.MIN_ORDER)
        return f"[GRID] {symbol} — SHORT @ {price} → {msg}"

    else:
        return f"[GRID] {symbol} — HOLD @ {price}"


