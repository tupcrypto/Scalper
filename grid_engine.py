import ccxt
from decimal import Decimal

# -----------------------------
# 1) CREATE CORRECT FUTURES EXCHANGE
# -----------------------------
def get_exchange(api_key, secret, password):
    exchange = ccxt.bitget({
        "apiKey": api_key,
        "secret": secret,
        "password": password,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",       # USDT perpetual futures
            "defaultSubType": "linear",  # Linear futures
            "hedgeMode": False,
        }
    })
    return exchange


# -----------------------------
# 2) FETCH FUTURES BALANCE
# -----------------------------
async def get_balance(exchange):
    try:
        balance = await exchange.fetch_balance()
        usdt = balance["total"].get("USDT", 0)
        return float(usdt)
    except Exception as e:
        return 0.0


# -----------------------------
# 3) FETCH FUTURES PRICE
# -----------------------------
async def get_price(exchange, pair):
    ticker = await exchange.fetch_ticker(pair)
    return float(ticker["last"])


# -----------------------------
# 4) SIMPLE GRID DECISION ENGINE
# -----------------------------
def check_grid(price):
    # Simplified logic: If price increasing → long entry
    # If price decreasing → short entry
    # Neutral → hold

    # You can improve later
    if price <= 0:
        return "HOLD"

    # Example fake logic
    if price % 2 == 0:
        return "LONG"
    else:
        return "SHORT"


# -----------------------------
# 5) EXECUTE ORDER (FUTURES)
# -----------------------------
async def execute_order(exchange, side, pair, usdt_amount):
    try:
        # format amount properly:
        cost = float(usdt_amount)

        # Bitget USDT futures wants:
        # amount = cost / price
        ticker = await exchange.fetch_ticker(pair)
        price = float(ticker["last"])
        qty_float = cost / price

        # Convert to Decimal with correct precision
        qty = Decimal(str(qty_float)).quantize(Decimal("0.0001"))

        # Execute ORDER
        order = await exchange.create_order(
            symbol=pair,
            type="market",
            side=side.lower(),
            amount=float(qty)  # Bitget expects numeric
        )
        return order

    except Exception as e:
        raise e
