# ======================================================
# grid_engine.py — FINAL STABLE VERSION
# ======================================================

import ccxt
import config


# ======================================
# GET EXCHANGE CLIENT (BITGET FUTURES)
# ======================================
def get_exchange():
    try:
        exchange = ccxt.bitget({
            "apiKey": config.BITGET_API_KEY,
            "secret": config.BITGET_API_SECRET,
            "password": config.BITGET_PASSPHRASE,
            "enableRateLimit": True,
            "options": {
                "defaultType": "swap",
                "createMarketBuyOrderRequiresPrice": False,
            },
        })
        exchange.load_markets()
        return exchange
    except Exception as e:
        print("EXCHANGE INIT ERROR:", str(e))
        return None


# ======================================
# GET BALANCE (TRY REAL FUTURES FIRST)
# ======================================
def get_balance(exchange):
    try:
        data = exchange.fetch_balance(params={"productType": "USDT-FUTURES"})
        usdt = data.get("USDT", {}).get("free", 0)
        return float(usdt)
    except Exception:
        # FALLBACK: assumed balance
        return float(config.ASSUMED_BALANCE_USDT)


# ======================================
# REQUIRED FUNCTION FOR BOT.PY
# ======================================
def get_assumed_balance(exchange):
    # bot.py expects this name — return real or fallback
    return get_balance(exchange)


# ======================================
# GET LIVE PRICE
# ======================================
def get_price(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return float(ticker["last"])
    except:
        return 0.0


# ======================================
# GRID SIGNAL (CENTER SHIFTING)
# ======================================
def get_grid_signal(exchange, symbol, balance):
    price = get_price(exchange, symbol)

    if price <= 0:
        return "NO DATA", price

    step_pct = float(config.GRID_STEP_PCT)   # e.g. 0.0015

    # static attribute to store center per symbol
    if not hasattr(get_grid_signal, "center"):
        get_grid_signal.center = {}

    # initialize first time
    if symbol not in get_grid_signal.center:
        get_grid_signal.center[symbol] = price
        return "INIT GRID — HOLD", price

    center = get_grid_signal.center[symbol]
    upper = center * (1 + step_pct)
    lower = center * (1 - step_pct)

    # Price breakout UP → SHORT
    if price >= upper:
        get_grid_signal.center[symbol] = price
        return "SHORT_ENTRY", price

    # Price breakout DOWN → LONG
    if price <= lower:
        get_grid_signal.center[symbol] = price
        return "LONG_ENTRY", price

    # Otherwise HOLD zone
    return "HOLD", price


# ======================================
# PLACE REAL FUTURES ORDER (BITGET SAFE)
# ======================================
def execute_market_order(exchange, symbol, signal, balance):
    if signal not in ["LONG_ENTRY", "SHORT_ENTRY"]:
        return "NO ORDER"

    # simulation mode
    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    # balance allocation
    num_pairs = len(config.PAIRS)
    pct = config.MAX_CAPITAL_PCT / 100.0
    calc_usdt = balance * pct / num_pairs

    # safe min cost to avoid reject
    trade_cost = max(5, calc_usdt)

    try:
        side = "buy" if signal == "LONG_ENTRY" else "sell"

        order = exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=None,
            params={
                "marginCoin": "USDT",
                "cost": trade_cost,
                "reduceOnly": False
            }
        )

        return f"ORDER OK: {order}"

    except Exception as e:
        return f"ORDER ERROR: {str(e)}"


# ======================================
# TOP-LEVEL GRID STEP CALLED BY BOT
# ======================================
def grid_step(exchange, symbol):
    balance = get_balance(exchange)
    signal, price = get_grid_signal(exchange, symbol, balance)
    result = execute_market_order(exchange, symbol, signal, balance)

    return f"[GRID] {symbol} — {signal} @ {price}\n{result}"
