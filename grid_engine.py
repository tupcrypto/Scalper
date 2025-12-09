# ======================================================
# grid_engine.py — FINAL STABLE VERSION FOR BITGET FUTURES
# ======================================================

import ccxt
import config

# Per-pair grid anchor
GRID_CENTER = {}


# ======================================================
# EXCHANGE CLIENT (BITGET)
# ======================================================
def get_exchange():
    try:
        ex = ccxt.bitget({
            "apiKey": config.BITGET_API_KEY,
            "secret": config.BITGET_API_SECRET,
            "password": config.BITGET_PASSPHRASE,
            "enableRateLimit": True,
            "options": {
                "defaultType": "swap",
                "createMarketBuyOrderRequiresPrice": False,
            },
        })
        ex.load_markets()
        return ex
    except Exception as e:
        print("EXCHANGE INIT ERROR:", e)
        return None


# ======================================================
# BALANCE (WE USE ASSUMED VALUE)
# ======================================================
def get_balance():
    """
    We intentionally use ASSUMED_BALANCE_USDT
    instead of live API balance.

    This eliminates:
    - futures wallet permission issues
    - unified account issues
    - region mismatches
    """
    return float(config.ASSUMED_BALANCE_USDT)


# ======================================================
# PRICE FETCH
# ======================================================
def get_price(exchange, symbol: str) -> float:
    try:
        ticker = exchange.fetch_ticker(symbol)
        return float(ticker["last"])
    except Exception as e:
        print(f"PRICE ERROR {symbol}: {e}")
        return 0.0


# ======================================================
# GRID SIGNAL (NEUTRAL PIONEX STYLE)
# ======================================================
def check_grid_signal(symbol: str, price: float, balance: float) -> str:
    if price <= 0:
        return "NO DATA"
    if balance <= 0:
        return "NO BALANCE"

    step = config.GRID_STEP_PCT  # e.g. 0.0015 = 0.15%

    # Initialize grid for this pair
    if symbol not in GRID_CENTER:
        GRID_CENTER[symbol] = price
        return "INIT GRID — HOLD"

    center = GRID_CENTER[symbol]
    upper = center * (1 + step)
    lower = center * (1 - step)

    # Price moved above upper threshold → short entry
    if price >= upper:
        GRID_CENTER[symbol] = price
        return f"SHORT_ENTRY @ {price}"

    # Price moved below lower threshold → long entry
    if price <= lower:
        GRID_CENTER[symbol] = price
        return f"LONG_ENTRY @ {price}"

    return "HOLD — Neutral zone"


# ======================================================
# ORDER EXECUTION — FIXED MIN SIZE PER PAIR
# ======================================================
def execute_order(exchange, symbol: str, signal: str, balance: float) -> str:
    """
    Uses cost-based market orders for Bitget futures.
    LIVE_TRADING = 0 → only simulate
    LIVE_TRADING = 1 → real trades
    """

    # No entry action → skip
    if "ENTRY" not in signal:
        return "NO ORDER"

    # Simulation mode
    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    # Safety check
    if balance <= 0:
        return "NO BALANCE"

    # Allocation logic:
    num_pairs = len(config.PAIRS)
    pct = config.MAX_CAPITAL_PCT / 100.0
    calc_usdt = balance * pct / num_pairs

    # =============================
    # ⭐ FIX: PAIR-SPECIFIC MIN SIZE
    # =============================
    # Because Bitget minimum cost per pair varies

    if symbol.startswith("SUI"):
        min_cost = 1     # works for small alt futures
    elif symbol.startswith("ETH"):
        min_cost = 3
    else:
        min_cost = 5     # safe minimum for BTC and majors

    # Final trade sizing
    trade_cost = max(min_cost, calc_usdt)

    # =============================
    # EXECUTE ORDER
    # =============================
    try:
        side = "buy" if "LONG_ENTRY" in signal else "sell"

        order = exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=None,               # we supply "cost" below
            params={
                "marginCoin": "USDT",
                "cost": trade_cost,
                "reduceOnly": False,
            },
        )

        return f"ORDER OK: {order}"

    except Exception as e:
        return f"ORDER ERROR: {e}"

