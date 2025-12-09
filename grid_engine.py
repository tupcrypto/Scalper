# ======================================================
# grid_engine.py — FINAL WORKING ORDER FIX VERSION
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
                "defaultType": "swap",              # USDT-M futures
                "createMarketBuyOrderRequiresPrice": False,
            },
        })
        ex.load_markets()
        return ex
    except Exception as e:
        print("EXCHANGE INIT ERROR:", e)
        return None


# ======================================================
# ASSUMED BALANCE
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
# ORDER EXECUTION — FIXED FOR 40808
# ======================================================
def execute_order(exchange, symbol: str, signal: str, balance: float) -> str:
    if "ENTRY" not in signal:
        return "NO ORDER"

    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    price = get_price(exchange, symbol)
    if price <= 0:
        return "BAD PRICE"

    # ==============================================
    # PAIR-SPECIFIC MINIMUM NOTIONAL
    # ==============================================
    if symbol.startswith("SUI"):
        min_cost_usdt = 5.5
    elif symbol.startswith("BTC"):
        min_cost_usdt = 9.5
    else:
        min_cost_usdt = 10.0

    # ==============================================
    # amount = cost / price
    # ==============================================
    raw_amount = min_cost_usdt / price

    # ==============================================
    # GET PRECISION FROM MARKET — **THE KEY FIX**
    # ==============================================
    try:
        market = exchange.market(symbol)
        precision = market.get("precision", {}).get("amount", 6)
        amount = round(raw_amount, precision)
    except:
        amount = float(f"{raw_amount:.6f}")

    # ==============================================
    # SET LEVERAGE
    # ==============================================
    try:
        exchange.set_leverage(
            leverage=5,
            symbol=symbol,
            params={"marginCoin": "USDT"},
        )
    except Exception as e:
        print(f"SET LEVERAGE ERROR {symbol}: {e}")

    # ==============================================
    # SET ISOLATED
    # ==============================================
    try:
        exchange.set_margin_mode(
            marginMode="isolated",
            symbol=symbol,
            params={"marginCoin": "USDT"},
        )
    except Exception as e:
        print(f"SET MARGIN MODE ERROR {symbol}: {e}")

    # ==============================================
    # PLACE MARKET ORDER — **NO extra params**
    # ==============================================
    try:
        side = "buy" if "LONG_ENTRY" in signal else "sell"

        order = exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=amount
        )

        return (
            f"ORDER OK: symbol={symbol}, "
            f"amount={amount}, "
            f"notional≈{min_cost_usdt}, "
            f"price≈{price}, "
            f"order={order}"
        )

    except Exception as e:
        return f"ORDER ERROR: {e}"
