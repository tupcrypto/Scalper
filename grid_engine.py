import ccxt
import config
import math


# ======================================================
# GET EXCHANGE INSTANCE
# ======================================================
def get_exchange():
    exchange = ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,   # BITGET NEEDS THIS
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",              # ensures futures mode
        }
    })
    return exchange


# ======================================================
# GET BALANCE — USDT futures wallet
# ======================================================
async def get_balance(exchange):
    try:
        balance = await exchange.fetch_balance()
        # futures balance extraction
        if "USDT" in balance:
            return float(balance["USDT"]["total"])

        if "future" in balance and "USDT" in balance["future"]:
            return float(balance["future"]["USDT"]["total"])

        return 0.0

    except Exception:
        return 0.0


# ======================================================
# PRICE FETCH
# ======================================================
async def get_price(exchange, pair):
    try:
        ticker = await exchange.fetch_ticker(pair)
        return float(ticker["last"])
    except Exception:
        return 0.0


# ======================================================
# GRID SIGNAL
# aggressive=True  → faster scalping
# aggressive=False → conservative
# ======================================================
def check_grid_signal(price, balance, aggressive=True):
    if price == 0:
        return "NO DATA"

    # grid sizing
    grid_pct = 0.003 if aggressive else 0.0015   # 0.3% vs 0.15%
    upper = price * (1 + grid_pct)
    lower = price * (1 - grid_pct)

    # center zone = HOLD
    if lower < price < upper:
        return "HOLD — Neutral zone"

    if price <= lower:
        return f"BUY @ {price}"

    if price >= upper:
        return f"SELL @ {price}"

    return "HOLD"


# ======================================================
# ORDER EXECUTION (ONLY IF LIVE)
# ======================================================
async def execute_order(exchange, pair, action, balance):
    size = balance * 0.10                   # fixed 10% of balance
    if size < 1:
        return "NO SIZE"

    if "BUY" in action:
        order = await exchange.create_market_buy_order(pair, size)
    elif "SELL" in action:
        order = await exchange.create_market_sell_order(pair, size)
    else:
        return "NO ORDER"

    return str(order)
