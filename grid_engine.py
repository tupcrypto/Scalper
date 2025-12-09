# ======================================================
# grid_engine.py — CLEAN SYNC GRID ENGINE FOR BITGET
# ======================================================

import ccxt
import config

# Per-pair grid center
GRID_CENTER = {}


# -----------------------------
# EXCHANGE CLIENT (BITGET)
# -----------------------------
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


# -----------------------------
# BALANCE (ASSUMED)
# -----------------------------
def get_balance():
    # we keep it simple and safe:
    # use your ASSUMED_BALANCE_USDT for sizing
    return float(config.ASSUMED_BALANCE_USDT)


# -----------------------------
# PRICE
# -----------------------------
def get_price(exchange, symbol: str) -> float:
    try:
        ticker = exchange.fetch_ticker(symbol)
        return float(ticker["last"])
    except Exception as e:
        print(f"PRICE ERROR {symbol}: {e}")
        return 0.0


# -----------------------------
# GRID SIGNAL (PIONEX-STYLE)
# -----------------------------
def check_grid_signal(symbol: str, price: float, balance: float) -> str:
    """
    Pseudo Pionex-neutral grid:
    - Keep a moving center per pair.
    - LONG_ENTRY when price moves GRID_STEP_PCT below center.
    - SHORT_ENTRY when price moves GRID_STEP_PCT above center.
    - Otherwise HOLD.
    """

    if price <= 0:
        return "NO DATA"
    if balance <= 0:
        return "NO BALANCE"

    step = config.GRID_STEP_PCT  # e.g. 0.0015 = 0.15%

    if symbol not in GRID_CENTER:
        GRID_CENTER[symbol] = price
        return "INIT GRID — HOLD"

    center = GRID_CENTER[symbol]
    upper = center * (1 + step)
    lower = center * (1 - step)

    if price >= upper:
        GRID_CENTER[symbol] = price
        return f"SHORT_ENTRY @ {price:.4f}"

    if price <= lower:
        GRID_CENTER[symbol] = price
        return f"LONG_ENTRY @ {price:.4f}"

    return "HOLD — Neutral zone"


# -----------------------------
# EXECUTE ORDER (BITGET FUTURES)
# -----------------------------
def execute_order(exchange, symbol: str, signal: str, balance: float) -> str:
    """
    Uses Bitget cost-based market orders:
    - We send 'cost' in USDT instead of 'amount'.
    """

    if "ENTRY" not in signal:
        return "NO ORDER"

    # simulation mode
    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    if balance <= 0:
        return "NO BALANCE"

    # capital allocation per pair
    num_pairs = max(1, len(config.PAIRS))
    pct = config.MAX_CAPITAL_PCT / 100.0
    calc_usdt = balance * pct / num_pairs

    trade_cost = max(5, calc_usdt)  # at least 5 USDT

    try:
        side = "buy" if "LONG_ENTRY" in signal else "sell"

        order = exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=None,
            params={
                "marginCoin": "USDT",
                "cost": trade_cost,
                "reduceOnly": False,
            },
        )

        return f"ORDER OK: {order}"

    except Exception as e:
        return f"ORDER ERROR: {e}"

