import ccxt.async_support as ccxt
import config

# ------------------------------------------------
# CREATE FUTURES EXCHANGE OBJECT
# ------------------------------------------------
async def get_exchange():
    exchange = ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",  # FUTURES account
        },
    })
    return exchange

# ------------------------------------------------
# GET REAL FUTURES BALANCE
# ------------------------------------------------
async def get_balance(exchange):
    try:
        # IMPORTANT — forces swap/futures balance
        balance = await exchange.fetch_balance({"type": "swap"})

        # 1️⃣ Primary futures location
        usdt = (
            balance.get("info", {})
                   .get("USDT", {})
                   .get("available", None)
        )

        # 2️⃣ Secondary mapping
        if usdt is None:
            usdt = balance.get("USDT", {}).get("free", None)

        # 3️⃣ If nothing matched → treat as zero
        if usdt is None:
            return 0.0

        return float(usdt)

    except Exception as e:
        print("BALANCE ERROR:", str(e))
        return 0.0

# ------------------------------------------------
# GET PRICE
# ------------------------------------------------
async def get_price(exchange, symbol):
    ticker = await exchange.fetch_ticker(symbol)
    return float(ticker["last"])

# ------------------------------------------------
# EXECUTE MARKET ORDER
# ------------------------------------------------
async def execute_order(exchange, symbol, side, cost):
    try:
        params = {"reduceOnly": False}

        order = await exchange.create_order(
            symbol=symbol,
            type="market",
            side=side.lower(),
            amount=cost,    # Bitget market uses cost NOT size
            params=params,
        )

        return order

    except Exception as e:
        print("ORDER ERROR:", str(e))
        return None

# ------------------------------------------------
# DECISION LOGIC
# ------------------------------------------------
async def grid_decision(price):
    # Basic test logic — you will improve later
    if price % 2 < 1:
        return "LONG"
    else:
        return "SHORT"

# ------------------------------------------------
# PER-SYMBOL EXECUTION
# ------------------------------------------------
async def process_symbol(exchange, symbol, balance):
    price = await get_price(exchange, symbol)

    if balance < config.MIN_ORDER.get(symbol, 5):
        return {
            "action": "NO ORDER",
            "price": price,
            "result": f"Balance {balance} too small"
        }

    action = await grid_decision(price)
    cost = config.MIN_ORDER[symbol]

    order = await execute_order(exchange, symbol, action, cost)

    if order:
        return {
            "action": action,
            "price": price,
            "result": f"ORDER EXECUTED: {cost} USDT"
        }
    else:
        return {
            "action": action,
            "price": price,
            "result": f"ORDER FAILED"
        }

