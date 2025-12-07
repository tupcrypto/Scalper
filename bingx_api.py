import math
import ccxt
import config


# =====================================================
#  EXCHANGE HELPER
# =====================================================

def get_exchange():
    """
    Returns a BingX futures (swap) client.
    """
    exchange = ccxt.bingx({
        "apiKey": config.BINGX_API_KEY,
        "secret": config.BINGX_API_SECRET,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",
        },
    })
    return exchange


def get_usdt_balance(exchange) -> float:
    """
    Approximate USDT futures balance.
    """
    try:
        balance = exchange.fetch_balance()
    except Exception as e:
        print("BALANCE ERROR:", e)
        return 0.0

    usdt_info = balance.get("USDT", {})
    free = usdt_info.get("free", 0.0)
    total = usdt_info.get("total", free)
    return float(total or free or 0.0)


def get_price(exchange, pair: str) -> float:
    """
    Fetch last price for symbol.
    """
    try:
        ticker = exchange.fetch_ticker(pair)
        return float(ticker["last"])
    except Exception as e:
        print(f"PRICE ERROR for {pair}:", e)
        return 0.0


def calc_amount_per_level(center_price: float, balance_usdt: float) -> float:
    """
    Calculate amount per grid level based on config.MAX_CAPITAL_PCT and config.GRID_LEVELS.
    """
    if center_price <= 0 or balance_usdt <= 0:
        return 0.0

    total_capital = balance_usdt * (config.MAX_CAPITAL_PCT / 100.0)
    if total_capital <= 0:
        return 0.0

    capital_per_level = total_capital / config.GRID_LEVELS
    notional_per_level = capital_per_level * config.LEVERAGE
    amount = notional_per_level / center_price

    # round down slightly for safety
    amount = math.floor(amount * 10000) / 10000
    return amount


# =====================================================
#  ORDER EXECUTION HELPERS
# =====================================================

def open_position(exchange, pair: str, side: str, amount: float) -> str:
    """
    Open a market position: side 'LONG' or 'SHORT'.
    """
    if amount <= 0:
        return "⚠️ Skipped order: amount <= 0"

    ccxt_side = "buy" if side == "LONG" else "sell"

    try:
        order = exchange.create_order(
            symbol=pair,
            type="market",
            side=ccxt_side,
            amount=amount,
            price=None,
            params={"leverage": config.LEVERAGE},
        )
    except Exception as e:
        return f"❌ OPEN {side} {pair} ERROR: {e}"

    return f"✅ OPEN {side} {pair} @ market, amount={amount}"


def close_position(exchange, pair: str, side: str, amount: float) -> str:
    """
    Close an existing position: side 'LONG' or 'SHORT' means what we are closing, 
    so we send the opposite ccxt side.
    """
    if amount <= 0:
        return "⚠️ Skipped close: amount <= 0"

    # If we are closing a LONG, we need to SELL. Closing a SHORT needs a BUY.
    ccxt_side = "sell" if side == "LONG" else "buy"

    try:
        order = exchange.create_order(
            symbol=pair,
            type="market",
            side=ccxt_side,
            amount=amount,
            price=None,
            params={"leverage": config.LEVERAGE},
        )
    except Exception as e:
        return f"❌ CLOSE {side} {pair} ERROR: {e}"

    return f"✅ CLOSE {side} {pair} @ market, amount={amount}"
