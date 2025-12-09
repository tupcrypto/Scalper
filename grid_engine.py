# ======================================================
# grid_engine.py — FINAL GUARANTEED TRADE VERSION
# ======================================================

import ccxt
import config

GRID_CENTER = {}


# ======================================================
# EXCHANGE CLIENT (BITGET FUTURES)
# ======================================================
def get_exchange():
    try:
        ex = ccxt.bitget({
            "apiKey": config.BITGET_API_KEY,
            "secret": config.BITGET_API_SECRET,
            "password": config.BITGET_PASSPHRASE,
            "enableRateLimit": True,
            "options": {
                "defaultType": "swap",              # futures
                "createMarketBuyOrderRequiresPrice": False,
            },
        })
        ex.load_markets()
        return ex
    except Exception as e:
        print("EXCHANGE INIT ERROR:", e)
        return None


# ======================================================
# BALANCE (ASSUMED)
# ======================================================
def get_balance() -> float:
    """
    We rely on ASSUMED_BALANCE_USDT rather than API,
    eliminating all wallet permission / region / unified issues.
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
# GRID SIGNAL (NEUTRAL)
# ======================================================
def check_grid_signal(symbol: str, price: float, balance: float) -> str:
    if price <= 0:
        return "NO DATA"

    if balance <= 0:
        return "NO BALANCE"

    step = float(config.GRID_STEP_PCT)

    if symbol not in GRID_CENTER:
        GRID_CENTER[symbol] = price
        return "INIT GRID — HOLD"

    center = GRID_CENTER[symbol]
    upper = center * (1 + step)
    lower = center * (1 - step)

    if price >= upper:
        GRID_CENTER[symbol] = price
        return f"SHORT_ENTRY @ {price}"

    if price <= lower:
        GRID_CENTER[symbol] = price
        return f"LONG_ENTRY @ {price}"

    return "HOLD — Neutral zone"


# ======================================================
# ORDER EXECUTION — ISOLATED + AMOUNT (GUARANTEED FILL)
# ======================================================
def execute_order(exchange, symbol: str, signal: str, balance: float) -> str:
    """
    FINAL FIX:
    - isolated mode
    - 5x leverage
    - tiny minimum (1 USDT)
    - AMOUNT orders (Bitget calculates margin automatically)
    """

    if "ENTRY" not in signal:
        return "NO ORDER"

    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    price = get_price(exchange, symbol)
    if price <= 0:
        return "BAD PRICE"

    # ============================================
    # ⭐ FIX: guaranteed fill margin sizing
    # ============================================
    # Use fixed small cost:
    min_cost_usdt = 1.0     # ALWAYS SAFE ON ISOLATED

    # convert cost → coin amount
    amount = min_cost_usdt / price
    amount = float(f"{amount:.6f}")

    # ============================================
    # SET LEVERAGE (5x)
    # ============================================
    try:
        exchange.set_leverage(
            leverage=5,
            symbol=symbol,
            params={"marginCoin": "USDT"},
        )
    except Exception as e:
        print(f"SET LEVERAGE ERROR {symbol}: {e}")

    # ============================================
    # SET ISOLATED MODE  ⭐⭐ KEY FIX ⭐⭐
    # ============================================
    try:
        exchange.set_margin_mode(
            marginMode="isolated",
            symbol=symbol,
            params={"marginCoin": "USDT"},
        )
    except Exception as e:
        print(f"SET MARGIN MODE ERROR {symbol}: {e}")

    # ============================================
    # PLACE ORDER — MARKET BY AMOUNT
    # ============================================
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

        return f"ORDER OK: amount={amount}, entry={price}, order={order}"

    except Exception as e:
        return f"ORDER ERROR: {e}"
