# ===========================
# grid_engine.py  (GRID BOT)
# ===========================
import asyncio
import ccxt
import config

# in-memory grid state: pair -> center price
GRID_STATE = {}


# ---------------------------
# EXCHANGE INSTANCE
# ---------------------------
def get_exchange():
    return ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",   # USDT-M futures
        },
    })


# ---------------------------
# BALANCE (ASSUMED)
# ---------------------------
def get_assumed_balance() -> float:
    return float(config.ASSUMED_BALANCE_USDT)


# ---------------------------
# PRICE
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
    Pseudo Pionex-style neutral grid:
    - Each pair has a grid center.
    - If price moves GRID_STEP_PCT above center → SHORT_ENTRY
    - If price moves GRID_STEP_PCT below center → LONG_ENTRY
    - After an entry, we shift center to current price.
    """

    price = float(price)
    balance = float(balance)

    if price <= 0:
        return "NO DATA"
    if balance <= 0:
        return "NO BALANCE"

    step_pct = config.GRID_STEP_PCT

    # Initialize center if not present
    if pair not in GRID_STATE:
        GRID_STATE[pair] = price
        return "INIT GRID — HOLD"

    center = GRID_STATE[pair]
    upper = center * (1 + step_pct)
    lower = center * (1 - step_pct)

    # Price went up enough above center → SHORT
    if price >= upper:
        GRID_STATE[pair] = price  # shift grid center up
        return f"SHORT_ENTRY @ {price:.4f}"

    # Price went down enough below center → LONG
    if price <= lower:
        GRID_STATE[pair] = price  # shift grid center down
        return f"LONG_ENTRY @ {price:.4f}"

    # Inside band → no action
    return "HOLD — Neutral zone"


# ---------------------------
# EXECUTE ORDER (if LIVE)
# ---------------------------
async def execute_order(exchange, pair: str, signal: str, balance: float) -> str:
    if "ENTRY" not in signal:
        return "NO ENTRY"

    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {pair}"

    if balance <= 0:
        return "NO BALANCE"

    # capital to use this cycle
    usdt_to_use = balance * (config.MAX_CAPITAL_PCT / 100.0)
    if usdt_to_use <= 0:
        return "NO CAPITAL"

    price = await get_price(exchange, pair)
    if price <= 0:
        return "BAD PRICE"

    # futures contract size (approx coins, not notional)
    amount = usdt_to_use / price

    side = "buy" if "LONG_ENTRY" in signal else "sell"

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
