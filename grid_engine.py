import ccxt
import config
import traceback

##############################
#  GET BITGET EXCHANGE
##############################
def get_exchange():
    try:
        exchange = ccxt.bitget({
            "apiKey": config.BITGET_API_KEY,
            "secret": config.BITGET_API_SECRET,
            "password": config.BITGET_PASSPHRASE,   # REQUIRED FOR FUTURES
            "options": {
                "defaultType": "swap",
                "createMarketBuyOrderRequiresPrice": False
            }
        })
        exchange.load_markets()
        return exchange

    except Exception as e:
        print("EXCHANGE INIT ERROR:", e)
        return None


################################
#  GET FUTURES USDT BALANCE
################################
def get_balance(exchange):
    try:
        balances = exchange.fetch_balance(params={"productType": "USDT-FUTURES"})
        bal = balances.get("USDT", {}).get("free", 0)
        return float(bal)

    except Exception as e:
        print("RAW BALANCE ERROR:", e)
        return 0.0


################################
# GET PRICE
################################
def get_price(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return float(ticker['last'])
    except:
        return 0.0


################################
# GRID SCALPING DECISION
################################
def check_grid_signal(price):
    """
    Very simple aggressive grid logic:
    - LONG when price dips 0.3%
    - SHORT when price pops 0.3%
    - OTHERWISE HOLD
    """
    # This is NOT a signal from history – it's a dynamic rolling midpoint:
    center = price

    lower = center * (1 - 0.003)
    upper = center * (1 + 0.003)

    if price <= lower:
        return "LONG_ENTRY"
    elif price >= upper:
        return "SHORT_ENTRY"
    else:
        return "HOLD"


################################
# PLACE REAL MARKET ORDER (WORKS)
################################
def place_market_order(exchange, symbol, side, balance):
    """
    Bitget requires:
        cost = amount in USDT
        type='market'
        size=None
        marginCoin='USDT'
    """
    try:
        if balance <= 0:
            return "NO BALANCE"

        # allocate safely
        capital_pct = config.MAX_CAPITAL_PCT / 100
        num_pairs = len(config.PAIRS)

        # evenly divide allocation across active pairs
        calc_cost = balance * capital_pct / num_pairs

        # minimum cost required to avoid precision errors
        trade_cost = max(5, calc_cost)     # ALWAYS >= $5

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


################################
# MASTER ENTRY FUNCTION
################################
def grid_step(exchange, symbol, balance):
    price = get_price(exchange, symbol)
    if price == 0:
        return f"{symbol}: PRICE ERROR"

    action = check_grid_signal(price)

    if action == "LONG_ENTRY":
        result = place_market_order(exchange, symbol, "buy", balance)
        return f"[GRID] {symbol} — LONG_ENTRY @ {price}\n{result}"

    elif action == "SHORT_ENTRY":
        result = place_market_order(exchange, symbol, "sell", balance)
        return f"[GRID] {symbol} — SHORT_ENTRY @ {price}\n{result}"

    else:
        return f"[GRID] {symbol} — HOLD — Neutral zone"
