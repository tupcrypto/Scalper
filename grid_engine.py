# ======================================================
# grid_engine.py — FINAL NEUTRAL FUTURES GRID BOT ENGINE
# ======================================================

import ccxt
import config


# ======================================
# GET BITGET FUTURES CLIENT
# ======================================
def get_exchange():
    try:
        exchange = ccxt.bitget({
            "apiKey": config.BITGET_API_KEY,
            "secret": config.BITGET_API_SECRET,
            "password": config.BITGET_PASSPHRASE,   # REQUIRED
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
# GET REAL FUTURES BALANCE (SAFE)
# ======================================
def get_balance(exchange):
    """
    Try to fetch actual futures wallet balance.
    If Bitget rejects it, fallback to assumed balance.
    """
    try:
        bal = exchange.fetch_balance(params={"productType": "USDT-FUTURES"})
        usdt = bal.get("USDT", {}).get("free", 0)
        return float(usdt)

    except Exception:
        # fallback to assumed
        return float(config.ASSUMED_BALANCE_USDT)


# ======================================
# REQUIRED FOR BOT.PY COMPATIBILITY
# ======================================
def get_assumed_balance(exchange):
    # this function name is required by bot.py
    return get_balance(exchange)


# ======================================
# FETCH PRICE
# ======================================
def get_price(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return float(ticker["last"])
    except:
        return 0.0


# ======================================
# GRID SIGNAL LOGIC (PIONEX STYLE)
# ======================================
def get_grid_signal(exchange, symbol, balance):
    """
    Neutral futures strategy:

    - If price dips below center → LONG_ENTRY
    - If price rises above center → SHORT_ENTRY
    - Otherwise HOLD

    We dynamically adjust grid center after each entry.
    """

    price = get_price(exchange, symbol)
    if price <= 0:
        return "NO DATA", price

    step_pct = config.GRID_STEP_PCT    # e.g. 0.0015 = 0.15%

    # initialize static center price per symbol
    if not hasattr(get_grid_signal, "center"):
        get_grid_signal.center = {}

    # FIRST RUN — center = current price
    if symbol not in get_grid_signal.center:
        get_grid_signal.center[symbol] = price
        return "INIT GRID — HOLD", price

    center = get_grid_signal.center[symbol]
    upper = center * (1 + step_pct)
    lower = center * (1 - step_pct)

    # Price up enough → SHORT
    if price >= upper:
        get_grid_signal.center[symbol] = price
        return "SHORT_ENTRY", price

    # Price down enough → LONG
    if price <= lower:
        get_grid_signal.center[symbol] = price
        return "LONG_ENTRY", price

    # NO ENTRY
    return "HOLD", price


# ======================================
# EXECUTE MARKET ORDER (BITGET SAFE)
# ======================================
def execute_market_order(exchange, symbol, signal, balance):
    """
    Bitget futures **REQUIRE cost instead of amount**
    We do:
        cost = max(5 USDT, allocated capital)
    """

    # NO ENTRY
    if signal not in ["LONG_ENTRY", "SHORT_ENTRY"]:
        return "NO ORDER"

    # paper mode
    if not config.LIVE_TRADING:
        return f"[SIMULATION] {signal} — {symbol}"

    # CAPITAL ALLOCATION
    num_pairs = len(config.PAIRS)
    pct = (config.MAX_CAPITAL_PCT / 100.0)

    calc_usdt = balance * pct / num_pairs
    trade_cost = max(5, calc_usdt)   # Bitget safe minimum

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
# MASTER GRID STEP — CALLED BY BOT LOOP
# ======================================
def grid_step(exchange, symbol):
    """
    Called every grid cycle from bot.py
    """

    # fetch balance
    balance = get_balance(exchange)

    # determine entry or hold
    signal, price = get_grid_signal(exchange, symbol, balance)

    # execute order if needed
    result = execute_market_order(exchange, symbol, signal, balance)

    # return message for telegram
    return f"[GRID] {symbol} — {signal} @ {price}\n{result}"
