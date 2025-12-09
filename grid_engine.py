# ===========================
# grid_engine.py  (GRID BOT)
# ===========================
import asyncio
import ccxt
import config

# in-memory grid center state
GRID_STATE = {}


# ---------------------------
# BITGET FUTURES CLIENT
# ---------------------------
def get_exchange():
    return ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",   # USDT perpetual futures
        },
    })


# ---------------------------
# ASSUMED BALANCE
# ---------------------------
def get_assumed_balance() -> float:
    return float(config.ASSUMED_BALANCE_USDT)


# ---------------------------
# FETCH PRICE
# ---------------------------
async def get_price(exchange, pair: str) -> float:
    try:
        ticker = await asyncio.to_thread(exchange.fetch_ticker, pair)
        return float(ticker["last"])
    except Exception as e:
        print(f"PRICE ERROR {pair}: {e}")
        return 0.0


# ---------------------------
# GRID SIGNAL (PIONEX-STYLE)
# ---------------------------
def check_grid_signal(pair: str, price: float, balance: float) -> str:
    """
    Neutral futures grid:
    - Initialize grid center if absent
    - LONG_ENTRY if price < lower band
    - SHORT_ENTRY if price > upper band
    - HOLD if inside band
    - After an entry, shift grid center to that price
    """
    price = float(price)
    balance = float(balance)

    if price <= 0:
        return "NO DATA"
    if balance <= 0:
        return "NO BALANCE"

    step_pct = config.GRID_STEP_PCT

    # first reference point
    if pair not in GRID_STATE:
        GRID_STATE[pair] = price
        return "INIT GRID — HOLD"

    center = GRID_STATE[pair]
    upper = center * (1 + step_pct)
    lower = center * (1 - step_pct)

    # UP MOVE → SHORT ENTRY
    if price >= upper:
        GRID_STATE[pair] = price    # shift grid center
        return f"SHORT_ENTRY @ {price:.4f}"

    # DOWN MOVE → LONG ENTRY
    if price <= lower:
        GRID_STATE[pair] = price    # shift grid center
        return f"LONG_ENTRY @ {price:.4f}"

    # inside band
    return "HOLD — Neutral zone"


# ---------------------------
# EXECUTE REAL FUTURES ORDER
# ---------------------------
async def execute_order(exchange, pair: str, signal: str, balance: float) -> str:
    if "ENTRY" not in signal:
        return "NO ENTRY"

    # Paper simulation
    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {pair}"

    if balance <= 0:
        return "NO BALANCE"

    # total notional we are allowed per trade
    usdt_to_use = balance * (config.MAX_CAPITAL_PCT / 100.0)
    if usdt_to_use <= 0:
        return "NO CAPITAL"

    price = await get_price(exchange, pair)
    if price <= 0:
        return "BAD PRICE"

    try:
        # LONG = BUY FUTURES
        if "LONG_ENTRY" in signal:
            params = {
                "cost": usdt_to_use,
                "createMarketBuyOrderRequiresPrice": False
            }

            order = await asyncio.to_thread(
                exchange.create_order,
                pair,
                "market",
                "buy",
                None,
                None,
                params
            )
            return f"ORDER OK: {order}"

        # SHORT = SELL FUTURES
        if "SHORT_ENTRY" in signal:
            amount = usdt_to_use / price

            order = await asyncio.to_thread(
                exchange.create_order,
                pair,
                "market",
                "sell",
                amount
            )
            return f"ORDER OK: {order}"

        return "NO ORDER"

    except Exception as e:
        return f"ORDER ERROR: {e}"
"
