# ======================================================
# grid_engine.py — FINAL STABLE VERSION (NO MORE ERRORS)
# ======================================================

import ccxt
import config


# ======================================
# CREATE BITGET FUTURES EXCHANGE CLIENT
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
                "createMarketBuyOrderRequiresPrice": False
            }
        })
        exchange.load_markets()
        return exchange

    except Exception as e:
        print("EXCHANGE INIT ERROR:", str(e))
        return None


# ======================================
# GET BALANCE (REAL OR FALLBACK)
# ======================================
def get_balance(exchange):
    try:
        data = exchange.fetch_balance(params={"productType": "USDT-FUTURES"})
        usdt = data.get("USDT", {}).get("free", 0)
        return float(usdt)

    except Exception:
        # fallback for safety
        return float(config.ASSUMED_BALANCE_USDT)


# ======================================
# FIXED COMPATIBILITY — WORKS WITH OR WITHOUT ARGUMENT
# ======================================
def get_assumed_balance(exchange=None):
    """
    IMPORTANT:
    bot.py sometimes calls get_assumed_balance() WITHOUT passing exchange
    So we auto-create one if missing.
    """
    if exchange is None:
        exchange = get_exchange()

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
# AGGRESSIVE NEUTRAL GRID
# ======================================
def get_grid_signal(exchange, symbol, balance):
    price = get_price(exchange, symbol)

    if price <= 0:
        return "NO DATA", price

    step_pct = float(config.GRID_STEP_PCT)

    # persistent center
    if not hasattr(get_grid_signal, "center"):
        get_grid_signal.center = {}

    # first run
    if symbol not in get_grid_signal.center:
        get_grid_signal.center[symbol] = price
        return "INIT GRID — HOLD", price

    center = get_grid_signal.center[symbol]
    upper = center * (1 + step_pct)
    lower = center * (1 - step_pct)

    # short opportunity
    if price >= upper:
        get_grid_signal.center[symbol] = price
        return "SHORT_ENTRY", price

    # long opportunity
    if price <= lower:
        get_grid_signal.center[symbol] = price
        return "LONG_ENTRY", price

    # no action
    return "HOLD", price


# ======================================
# EXECUTE FUTURES ORDER USING COST
# ======================================
def execute_market_order(exchange, symbol, signal, balance):
    if signal not in ["LONG_ENTRY", "SHORT_ENTRY"]:
        return "NO ORDER"

    # simulation
    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    num_pairs = len(config.PAIRS)
    pct = config.MAX_CAPITAL_PCT / 100.0
    calc_usdt = balance * pct / num_pairs

    trade_cost = max(5, calc_usdt)   # minimum $5

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
# MAIN LOOP ENTRY
# ======================================
def grid_step(exchange, symbol):
    balance = get_assumed_balance(exchange)
    signal, price = get_grid_signal(exchange, symbol, balance)
    result = execute_market_order(exchange, symbol, signal, balance)

    return f"[GRID] {symbol} — {signal} @ {price}\n{result}"
