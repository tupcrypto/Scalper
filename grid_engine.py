# ======================================================
# grid_engine.py — FINAL CLEAN VERSION FOR BITGET FUTURES
# ======================================================

import ccxt
import config

# Per-pair grid center (anchor price)
GRID_CENTER = {}


# ======================================================
# EXCHANGE CLIENT (BITGET USDT-M FUTURES)
# ======================================================
def get_exchange():
    try:
        ex = ccxt.bitget({
            "apiKey": config.BITGET_API_KEY,
            "secret": config.BITGET_API_SECRET,
            "password": config.BITGET_PASSPHRASE,
            "enableRateLimit": True,
            "options": {
                "defaultType": "swap",              # USDT-M perpetuals
                "createMarketBuyOrderRequiresPrice": False,
            },
        })
        ex.load_markets()
        return ex
    except Exception as e:
        print("EXCHANGE INIT ERROR:", e)
        return None


# ======================================================
# BALANCE (ASSUMED — FROM ENV, NOT API)
# ======================================================
def get_balance() -> float:
    """
    We trust ASSUMED_BALANCE_USDT from config.
    This avoids all Bitget balance / permission / wallet issues.
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
# GRID SIGNAL (PIONEX-STYLE NEUTRAL LOGIC)
# ======================================================
def check_grid_signal(symbol: str, price: float, balance: float) -> str:
    """
    Very simple neutral grid:

    - Keep a moving center per pair.
    - If price moves GRID_STEP_PCT above center → SHORT_ENTRY
    - If price moves GRID_STEP_PCT below center → LONG_ENTRY
    - Otherwise → HOLD
    """
    if price <= 0:
        return "NO DATA"
    if balance <= 0:
        return "NO BALANCE"

    step = float(config.GRID_STEP_PCT)  # e.g. 0.0015 = 0.15%

    # Initialize center on first tick for this symbol
    if symbol not in GRID_CENTER:
        GRID_CENTER[symbol] = price
        return "INIT GRID — HOLD"

    center = GRID_CENTER[symbol]
    upper = center * (1 + step)
    lower = center * (1 - step)

    # Price broke above upper band → short entry
    if price >= upper:
        GRID_CENTER[symbol] = price
        return f"SHORT_ENTRY @ {price}"

    # Price broke below lower band → long entry
    if price <= lower:
        GRID_CENTER[symbol] = price
        return f"LONG_ENTRY @ {price}"

    # Inside band → no action
    return "HOLD — Neutral zone"


# ======================================================
# ORDER EXECUTION — BITGET FUTURES VIA AMOUNT (NOT COST)
# ======================================================
def execute_order(exchange, symbol: str, signal: str, balance: float) -> str:
    """
    Places a Bitget USDT-M futures market order using AMOUNT (coin qty),
    after setting leverage & cross margin.

    LIVE_TRADING = 0  → only simulate, no real order
    LIVE_TRADING = 1  → place actual orders
    """

    # No entry signal → skip
    if "ENTRY" not in signal:
        return "NO ORDER"

    # Simulation mode → just return text
    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    if balance <= 0:
        return "NO BALANCE"

    # ------------------------------------------------------------------
    # 1) CAPITAL ALLOCATION (IN USDT)
    # ------------------------------------------------------------------
    num_pairs = max(1, len(config.PAIRS))
    pct = float(config.MAX_CAPITAL_PCT) / 100.0

    # USDT allocated to this pair
    allocated_usdt = balance * pct / num_pairs

    # ------------------------------------------------------------------
    # 2) FETCH LATEST PRICE TO CONVERT USDT → COIN AMOUNT
    # ------------------------------------------------------------------
    price = get_price(exchange, symbol)
    if price <= 0:
        return "BAD PRICE"

    # ------------------------------------------------------------------
    # 3) MINIMUM COIN AMOUNT PER PAIR
    # ------------------------------------------------------------------
    # These are rough safe minimums; Bitget will accept them on 5x cross
    if symbol.startswith("SUI"):
        min_amount = 1.0         # 1 SUI
    elif symbol.startswith("ETH"):
        min_amount = 0.001       # 0.001 ETH
    else:
        min_amount = 0.0001      # e.g. BTC: 0.0001 BTC

    # Amount in coins = allocated_usdt / price, but not below min_amount
    raw_amount = allocated_usdt / price
    amount = max(min_amount, raw_amount)

    # Just in case: round to 6 decimals to avoid precision issues
    amount = float(f"{amount:.6f}")

    # ------------------------------------------------------------------
    # 4) SET LEVERAGE & MARGIN MODE (REQUIRED BY BITGET)
    # ------------------------------------------------------------------
    try:
        # Set leverage (e.g. 5x)
        exchange.set_leverage(
            leverage=5,
            symbol=symbol,
            params={"marginCoin": "USDT"},
        )
    except Exception as e:
        print(f"SET LEVERAGE ERROR {symbol}: {e}")

    try:
        # Cross margin mode
        exchange.set_margin_mode(
            marginMode="cross",
            symbol=symbol,
            params={"marginCoin": "USDT"},
        )
    except Exception as e:
        print(f"SET MARGIN MODE ERROR {symbol}: {e}")

    # ------------------------------------------------------------------
    # 5) PLACE MARKET ORDER BY AMOUNT
    # ------------------------------------------------------------------
    try:
        side = "buy" if "LONG_ENTRY" in signal else "sell"

        order = exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=amount,
            params={
                "marginCoin": "USDT",
                "reduceOnly": False,
            },
        )

        return f"ORDER OK: {order}"

    except Exception as e:
        return f"ORDER ERROR: {e}"
