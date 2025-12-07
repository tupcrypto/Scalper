import math
import ccxt
import config


# =====================================================
#  EXCHANGE HELPER
# =====================================================

def get_exchange():
    exchange = ccxt.bingx({
        "apiKey": config.BINGX_API_KEY,
        "secret": config.BINGX_API_SECRET,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",
        },
    })
    return exchange


# =====================================================
#  BALANCE & POSITION SIZING
# =====================================================

def get_usdt_balance(exchange) -> float:
    balance = exchange.fetch_balance()
    usdt_info = balance.get("USDT", {})
    free = usdt_info.get("free", 0.0)
    total = usdt_info.get("total", free)
    return float(total or free or 0.0)


def calc_order_amount(entry_price: float, balance_usdt: float) -> float:
    if entry_price <= 0 or balance_usdt <= 0:
        return 0.0

    capital_to_use = balance_usdt * (config.MAX_CAPITAL_PCT / 100.0)
    notional = capital_to_use * config.LEVERAGE

    amount = notional / entry_price
    amount = math.floor(amount * 10000) / 10000
    return amount


# =====================================================
#  MAIN: EXECUTE TRADE FROM SIGNAL
# =====================================================

def execute_trade_from_signal(signal: dict) -> dict:
    """
    Takes a signal dict from grid_engine.get_scalp_signal and places a trade.
    """
    pair = signal.get("pair", config.PAIR)
    exchange = get_exchange()

    balance_usdt = get_usdt_balance(exchange)
    if balance_usdt <= 0:
        return {"ok": False, "message": "❌ LIVE TRADE FAILED: No USDT futures balance."}

    entry_price = float(signal["entry"])
    amount = calc_order_amount(entry_price, balance_usdt)
    if amount <= 0:
        return {"ok": False, "message": "❌ LIVE TRADE FAILED: Position size <= 0."}

    side = "buy" if signal["side"] == "LONG" else "sell"
    tp = float(signal["tp"])
    sl = float(signal["sl"])

    params = {
        "stopLossPrice": sl,
        "takeProfitPrice": tp,
        "leverage": config.LEVERAGE,
    }

    try:
        order = exchange.create_order(
            symbol=pair,
            type="market",
            side=side,
            amount=amount,
            price=None,
            params=params,
        )
    except Exception as e:
        return {"ok": False, "message": f"❌ LIVE TRADE ERROR: {e}"}

    msg = (
        f"✅ LIVE TRADE EXECUTED on BingX\n"
        f"Pair: {pair}\n"
        f"Side: {signal['side']}\n"
        f"Amount: {amount}\n"
        f"Entry (approx): {entry_price:.4f}\n"
        f"TP: {tp:.4f}\n"
        f"SL: {sl:.4f}\n"
        f"Leverage: {config.LEVERAGE}x\n"
        f"Capital per trade: {config.MAX_CAPITAL_PCT}%"
    )

    return {"ok": True, "message": msg, "order": order}
