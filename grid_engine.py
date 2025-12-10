import ccxt
from decimal import Decimal, ROUND_DOWN
import config
import math

# ===========================================================
#  EXCHANGE INITIALIZATION (ONLY THIS FIXES 40014 FOREVER)
# ===========================================================
def get_exchange():
    exchange = ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",        # 100% REQUIRED (Futures mode)
            "createMarketBuyOrderRequiresPrice": False,
        }
    })
    return exchange


# ===========================================================
#  FETCH BALANCE (USDT FUTURES)
# ===========================================================
async def get_balance(exchange):
    try:
        balance = await exchange.fetch_balance()
        usdt = balance["total"].get("USDT", 0)
        return float(usdt)
    except:
        return 0.0


# ===========================================================
#  FETCH PRICE (FUTURES)
# ===========================================================
async def get_price(exchange, symbol):
    ticker = await exchange.fetch_ticker(symbol)
    return float(ticker["last"])


# ===========================================================
#  GRID DECISION ENGINE (you can improve later)
# ===========================================================
def decide_action(price):
    if price <= 0:
        return "HOLD"

    # very simple neutral fake logic for testing
    # replace later with AI logic
    if math.floor(price) % 2 == 0:
        return "LONG"
    else:
        return "SHORT"


# ===========================================================
#  EXECUTE MARKET ORDER (FUTURES)
# ===========================================================
async def execute_order(exchange, symbol, side, usdt_amount):
    try:
        # get price to compute quantity
        ticker = await exchange.fetch_ticker(symbol)
        price = float(ticker["last"])

        # Compute quantity
        qty_float = usdt_amount / price

        # Round to valid precision
        qty = Decimal(str(qty_float)).quantize(Decimal("0.0001"), rounding=ROUND_DOWN)

        # Execute order
        order = await exchange.create_order(
            symbol=symbol,
            type="market",
            side=side.lower(),
            amount=float(qty),
        )

        return order

    except Exception as e:
        raise e


# ===========================================================
#  PER-PAIR GRID ACTION LOGIC (USED BY scan & start)
# ===========================================================
async def trade_symbol(exchange, symbol, balance):
    try:
        price = await get_price(exchange, symbol)

        # REQUIRED: minimum order size per pair
        min_cost = config.MIN_ORDER_USDT.get(symbol, 10)

        # If no balance, no trades
        if balance < min_cost:
            return {
                "price": price,
                "action": "NO ORDER",
                "result": "Insufficient balance"
            }

        # Decide action
        action = decide_action(price)

        if action == "HOLD":
            return {
                "price": price,
                "action": "HOLD",
                "result": "Neutral zone"
            }

        # Amount to use each trade
        # Use % of balance defined in config
        usdt_alloc = (balance * config.RISK_PER_TRADE_PCT) / 100

        if usdt_alloc < min_cost:
            usdt_alloc = min_cost

        # EXECUTE IF LIVE TRADING ENABLED
        if config.LIVE_TRADING:
            order = await execute_order(exchange, symbol, action, usdt_alloc)
            return {
                "price": price,
                "action": action,
                "result": f"ORDER EXECUTED: {order}"
            }
        else:
            return {
                "price": price,
                "action": action,
                "result": f"(SIMULATION) Would execute {action} with {usdt_alloc:.2f} USDT"
            }

    except Exception as e:
        return {
            "price": 0,
            "action": "ERROR",
            "result": str(e)
        }
