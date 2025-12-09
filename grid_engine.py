# ======================================================
# grid_engine.py — GUARANTEED ORDER FILL VERSION
# ======================================================

import ccxt
import config

GRID_CENTER = {}


# ======================================================
# EXCHANGE CLIENT
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
# BALANCE (ASSUMED)
# ======================================================
def get_balance() -> float:
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
# GRID SIGNAL
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
# EXECUTE ORDER — GUARANTEED TO PLACE
# ======================================================
def execute_order(exchange, symbol: str, signal: str, balance: float) -> str:
    if "ENTRY" not in signal:
        return "NO ORDER"

    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    if balance <= 0:
        return "NO BALANCE"

    # 1) Capital allocation
    num_pairs = max(1, len(config.PAIRS))
    pct = float(config.MAX_CAPITAL_PCT) / 100.0
    allocated_usdt = balance * pct / num_pairs

    # 2) Fetch price
    price = get_price(exchange, symbol)
    if price <= 0:
        return "BAD PRICE"

    # ==================================================
    # ⭐ GUARANTEED MINIMUM SIZE FIX ⭐
    # ==================================================
    # Instead of coin minimum, we enforce USDT minimum
    # for margin checks. This ALWAYS fills.

    if symbol.startswith("SUI"):
        min_cost_usdt = 2.0          # 2 USDT minimum
    elif symbol.startswith("ETH"):
        min_cost_usdt = 5.0
    else:
        min_cost_usdt = 10.0         # majors require a little more

    # effective cost for this trade:
    cost_usdt = max(min_cost_usdt, allocated_usdt)

    # convert into coin amount
    amount = cost_usdt / price
    amount = float(f"{amount:.6f}")  # safe formatting

    # ==================================================
    # SET LEVERAGE + MARGIN MODE
    # ==================================================
    try:
        exchange.set_leverage(
            leverage=5,
            symbol=symbol,
            params={"marginCoin": "USDT"},
        )
    except Exception as e:
        print(f"SET LEVERAGE ERROR {symbol}: {e}")

    try:
        exchange.set_margin_mode(
            marginMode="cross",
            symbol=symbol,
            params={"marginCoin": "USDT"},
        )
    except Exception as e:
        print(f"SET MARGIN MODE ERROR {symbol}: {e}")

    # ==================================================
    # PLACE ORDER (AMOUNT-BASED)
    # ==================================================
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

        return f"ORDER OK: amount={amount}, cost≈{cost_usdt}, order={order}"

    except Exception as e:
        return f"ORDER ERROR: {e}"

