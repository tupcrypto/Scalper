# ======================================================
# grid_engine.py — FINAL FINAL FIX
# ======================================================

import ccxt
import config

GRID_CENTER = {}


# ======================================================
# CLIENT
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
# BALANCE
# ======================================================
def get_balance():
    return float(config.ASSUMED_BALANCE_USDT)


# ======================================================
# PRICE
# ======================================================
def get_price(exchange, symbol):
    try:
        t = exchange.fetch_ticker(symbol)
        return float(t["last"])
    except Exception as e:
        print(f"PRICE ERROR {symbol}: {e}")
        return 0.0


# ======================================================
# GRID SIGNAL
# ======================================================
def check_grid_signal(symbol, price, balance):
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
# ORDER EXECUTION **NO SIZE, NO DECIMAL, NO PRECISION**
# ======================================================
def execute_order(exchange, symbol, signal, balance):
    if "ENTRY" not in signal:
        return "NO ORDER"

    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    price = get_price(exchange, symbol)
    if price <= 0:
        return "BAD PRICE"

    # --------------------------
    # MINIMUM NOTIONAL COST
    # --------------------------
    if symbol.startswith("SUI"):
        min_cost_usdt = 5.5
    elif symbol.startswith("BTC"):
        min_cost_usdt = 9.5
    else:
        min_cost_usdt = 10.0

    # --------------------------
    # TRY ENTRY WITH COST INSTEAD OF SIZE ⭐⭐⭐
    # --------------------------
    try:
        # Leverage
        try:
            exchange.set_leverage(
                leverage=5,
                symbol=symbol,
                params={"marginCoin": "USDT"},
            )
        except:
            pass

        # Isolated
        try:
            exchange.set_margin_mode(
                marginMode="isolated",
                symbol=symbol,
                params={"marginCoin": "USDT"},
            )
        except:
            pass

        # market order using COST (not SIZE!)
        side = "buy" if "LONG_ENTRY" in signal else "sell"

        order = exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=None,
            price=None,
            params={
                "marginCoin": "USDT",
                "cost": min_cost_usdt,     # ⭐⭐ THE FIX ⭐⭐
                "force": "normal",
            },
        )

        return (
            f"ORDER OK: {symbol}, cost={min_cost_usdt}, price≈{price}, order={order}"
        )

    except Exception as e:
        return f"ORDER ERROR: {e}"

