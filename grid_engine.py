# ===========================
# grid_engine.py  (FINAL)
# ===========================
import asyncio
import ccxt
import config

_exchange = None


# -------------------------------------------------------
# EXCHANGE INSTANCE (BITGET USDT-M FUTURES)
# -------------------------------------------------------
def get_exchange():
    global _exchange
    if _exchange is None:
        _exchange = ccxt.bitget({
            "apiKey": config.BITGET_API_KEY,
            "secret": config.BITGET_API_SECRET,
            "password": config.BITGET_PASSPHRASE,
            "enableRateLimit": True,
            "options": {
                "defaultType": "swap",   # USDT-M perpetual / futures
            },
        })
    return _exchange


# -------------------------------------------------------
# FUTURES BALANCE (USDT)
# -------------------------------------------------------
async def get_balance(exchange) -> float:
    try:
        # run sync ccxt call on a thread
        bal = await asyncio.to_thread(exchange.fetch_balance, {"type": "swap"})

        # Bitget usually has: bal["USDT"] = { free, used, total, ... }
        if "USDT" in bal and isinstance(bal["USDT"], dict):
            usdt_info = bal["USDT"]
            if "free" in usdt_info:
                return float(usdt_info["free"])
            if "total" in usdt_info:
                return float(usdt_info["total"])

        # fallback
        return 0.0

    except Exception as e:
        # optional: print or log
        print(f"BALANCE ERROR: {e}")
        return 0.0


# -------------------------------------------------------
# PRICE FETCH
# -------------------------------------------------------
async def get_price(exchange, pair: str) -> float:
    try:
        ticker = await asyncio.to_thread(exchange.fetch_ticker, pair)
        return float(ticker["last"])
    except Exception as e:
        print(f"PRICE ERROR {pair}: {e}")
        return 0.0


# -------------------------------------------------------
# GRID SIGNAL LOGIC
# aggressive=True  -> wider/faster scalping band
# -------------------------------------------------------
def check_grid_signal(price: float, balance: float, aggressive: bool = True) -> str:
    if price <= 0:
        return "NO DATA"
    if balance <= 0:
        return "NO BALANCE"

    band = 0.003 if aggressive else 0.0015  # 0.3% vs 0.15%
    upper = price * (1 + band)
    lower = price * (1 - band)

    if lower < price < upper:
        return "HOLD — Neutral zone"

    if price <= lower:
        return f"BUY SIGNAL @ {price:.4f}"

    if price >= upper:
        return f"SELL SIGNAL @ {price:.4f}"

    return "HOLD"


# -------------------------------------------------------
# ORDER EXECUTION (ONLY IF LIVE_TRADING = True)
# -------------------------------------------------------
async def execute_order(exchange, pair: str, action: str, balance: float) -> str:
    if not config.LIVE_TRADING:
        return "LIVE_TRADING=0 -> signal only"

    if balance <= 0:
        return "NO BALANCE"

    # capital to deploy this cycle
    usdt_to_use = balance * (config.MAX_CAPITAL_PCT / 100.0)
    if usdt_to_use <= 0:
        return "NO CAPITAL"

    price = await get_price(exchange, pair)
    if price <= 0:
        return "BAD PRICE"

    amount = usdt_to_use / price
    side = "buy" if "BUY" in action else "sell"

    try:
        order = await asyncio.to_thread(
            exchange.create_order,
            pair,
            "market",
            side,
            amount
        )
        return f"ORDER OK: {order}"
    except Exception as e:
        return f"ORDER ERROR: {e}"
