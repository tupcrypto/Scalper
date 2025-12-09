# ======================================================
# grid_engine.py — FINAL FULL ASYNC COMPATIBLE VERSION
# ======================================================

import ccxt
import config


# ======================================
# EXCHANGE CLIENT
# ======================================
def get_exchange():
    try:
        exchange = ccxt.bitget({
            "apiKey": config.BITGET_API_KEY,
            "secret": config.BITGET_API_SECRET,
            "password": config.BITGET_PASSPHRASE,
            "options": {
                "defaultType": "swap",
                "createMarketBuyOrderRequiresPrice": False
            },
            "enableRateLimit": True
        })
        exchange.load_markets()
        return exchange

    except Exception as e:
        print("EXCHANGE INIT ERROR:", str(e))
        return None


# ======================================
# SYNC BALANCE READER
# ======================================
def get_balance(exchange):
    try:
        data = exchange.fetch_balance(params={"productType": "USDT-FUTURES"})
        usdt = data.get("USDT", {}).get("free", 0)
        return float(usdt)
    except Exception:
        return float(config.ASSUMED_BALANCE_USDT)


# ======================================
# ASYNC BALANCE WRAPPER — BOT COMPATIBLE
# ======================================
async def get_assumed_balance(exchange=None):
    """
    bot.py may do:
        await grid_engine.get_assumed_balance()

    OR:

        await grid_engine.get_assumed_balance(exchange)

    So:
      - exchange optional
      - async compatible
    """
    if exchange is None:
        exchange = get_exchange()

    bal = get_balance(exchange)
    return bal


# ======================================
# PRICE READER
# ======================================
def get_price(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return float(ticker["last"])
    except:
        return 0.0


# ======================================
# AGGRESSIVE NEUTRAL GRID SIGNAL
# ======================================
def get_grid_signal(exchange, symbol, balance):
    price = get_price(exchange, symbol)

    if price <= 0:
        return "NO DATA", price

    step_pct = float(config.GRID_STEP_PCT)

    if not hasattr(get_grid_signal, "center"):
        get_grid_signal.center = {}

    if symbol not in get_grid_signal.center:
        get_grid_signal.center[symbol] = price
        return "INIT GRID — HOLD", price

    center = get_grid_signal.center[symbol]
    upper = center * (1 + step_pct)
    lower = center * (1 - step_pct)

    if price >= upper:
        get_grid_signal.center[symbol] = price
        return "SHORT_ENTRY", price

    if price <= lower:
        get_grid_signal.center[symbol] = price
        return "LONG_ENTRY", price

    return "HOLD", price


# ======================================
# SAFE FUTURES ORDER EXECUTION USING COST
# ======================================
def execute_market_order(exchange, symbol, signal, balance):
    if signal not in ["LONG_ENTRY", "SHORT_ENTRY"]:
        return "NO ORDER"

    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    num_pairs = len(config.PAIRS)
    pct = config.MAX_CAPITAL_PCT / 100.0

    calc_usdt = balance * pct / num_pairs
    trade_cost = max(5, calc_usdt)

    try:
        side = "buy" if signal == "LONG_ENTRY" else "sell"

        order = exchange.create_order(
            symbol=symbol,
            type='market',
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
# MAIN GRID STEP FOR BOT LOOP (ASYNC SAFE)
# ======================================
async def grid_step(exchange, symbol):
    balance = await get_assumed_balance(exchange)
    signal, price = get_grid_signal(exchange, symbol, balance)
    result = execute_market_order(exchange, symbol, signal, balance)

    return f"[GRID] {symbol} — {signal} @ {price}\n{result}"

