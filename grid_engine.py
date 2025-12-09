# ===========================
# grid_engine.py  (GRID BOT CLEAN)
# ===========================
import asyncio
import ccxt
import config

# In-memory grid center per pair
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
            "defaultType": "swap",   # USDT-M perpetual futures
            "createMarketBuyOrderRequiresPrice": False,
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
# GRID SIGNAL (NEUTRAL GRID)
# ---------------------------
def check_grid_signal(pair: str, price: float, balance: float) -> str:
    """
    Neutral futures grid:
    - Each pair has a center price.
    - If price moves above center by GRID_STEP_PCT -> SHORT_ENTRY.
    - If price moves below center by GRID_STEP_PCT -> LONG_ENTRY.
    - After an entry, we shift the center to the new price.
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

    # Price went up enough -> short
    if price >= upper:
        GRID_STATE[pair] = price
        return f"SHORT_ENTRY @ {price:.4f}"

    # Price went down enough -> long
    if price <= lower:
        GRID_STATE[pair] = price
        return f"LONG_ENTRY @ {price:.4f}"

    # Inside band
    return "HOLD — Neutral zone"


# ---------------------------
# EXECUTE REAL FUTURES ORDER
# ---------------------------
async def execute_order(exchange, pair: str, signal: str, balance: float) -> str:
    """
    Executes Bitget futures orders.

    LONG_ENTRY  -> market buy
    SHORT_ENTRY -> market sell
    Uses MAX_CAPITAL_PCT of ASSUMED_BALANCE_USDT per trade.
    """
    if "ENTRY" not in signal:
        return "NO ENTRY"

    # Paper mode
    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {pair}"

    if balance <= 0:
        return "NO BALANCE"

    # Capital for this trade
    usdt_to_use = balance * (config.MAX_CAPITAL_PCT / 100.0)
    if usdt_to_use <= 0:
        return "NO CAPITAL"

    price = await get_price(exchange, pair)
    if price <= 0:
        return "BAD PRICE"

    try:
        # LONG = BUY futures
        if "LONG_ENTRY" in signal:
            # Number of contracts (approx coins)
            amount = usdt_to_use / price
            params = {
                "createMarketBuyOrderRequiresPrice": False,
            }
            order = await asyncio.to_thread(
                exchange.create_order,
                pair,
                "market",
                "buy",
                amount,
                None,
                params,
            )
            return f"ORDER OK: {order}"

        # SHORT = SELL futures
        if "SHORT_ENTRY" in signal:
            amount = usdt_to_use / price
            order = await asyncio.to_thread(
                exchange.create_order,
                pair,
                "market",
                "sell",
                amount,
            )
            return f"ORDER OK: {order}"

        return "NO ORDER"

    except Exception as e:
        return f"ORDER ERROR: {e}"
