import math
import ccxt
import config


# =====================================================
#  EXCHANGE HELPER
# =====================================================

def get_exchange():
    """
    Returns a ccxt BingX futures (swap) client.
    Make sure your API keys have futures trading enabled.
    """
    exchange = ccxt.bingx({
        "apiKey": config.BINGX_API_KEY,
        "secret": config.BINGX_API_SECRET,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",  # futures / perpetual swaps
        },
    })
    return exchange


# =====================================================
#  BALANCE & POSITION SIZING
# =====================================================

def get_usdt_balance(exchange) -> float:
    """
    Fetch futures USDT balance (approx).
    """
    balance = exchange.fetch_balance()
    # ccxt usually puts major balances under symbol keys
    usdt_info = balance.get("USDT", {})
    free = usdt_info.get("free", 0.0)
    total = usdt_info.get("total", free)
    return float(total or free or 0.0)


def calc_order_amount(entry_price: float, balance_usdt: float) -> float:
    """
    Calculate position size (amount of coin) based on balance, leverage, and risk settings.
    """
    if entry_price <= 0 or balance_usdt <= 0:
        return 0.0

    # Capital allocated per trade
    capital_to_use = balance_usdt * (config.MAX_CAPITAL_PCT / 100.0)

    # with leverage, notional = capital * leverage
    notional = capital_to_use * config.LEVERAGE

    amount = notional / entry_price
    # round to 4 decimal places for BTC/USDT, adjust if needed
    amount = math.floor(amount * 10000) / 10000
    return amount


# =====================================================
#  MAIN: EXECUTE TRADE FROM SIGNAL
# =====================================================

def execute_trade_from_signal(signal: dict) -> dict:
    """
    Takes a signal dict from grid_engine.get_scalp_signal and actually places a trade
    on BingX futures using ccxt.
    Returns dict with 'ok': bool, and 'message': str for Telegram.
    """
    exchange = get_exchange()

    # 1) Fetch balance
    balance_usdt = get_usdt_balance(exchange)
    if balance_usdt <= 0:
        return {
            "ok": False,
            "message": "❌ LIVE TRADE FAILED: No USDT futures balance detected."
        }

    entry_price = float(signal["entry"])
    amount = calc_order_amount(entry_price, balance_usdt)
    if amount <= 0:
        return {
            "ok": False,
            "message": "❌ LIVE TRADE FAILED: Position size <= 0 (check balance / settings)."
        }

    side = "buy" if signal["side"] == "LONG" else "sell"
    tp = float(signal["tp"])
    sl = float(signal["sl"])

    params = {
        # Many ccxt futures exchanges accept these unified params.
        # If BingX rejects them, the main order should still open.
        "stopLossPrice": sl,
        "takeProfitPrice": tp,
        "leverage": config.LEVERAGE,
        # You may need extra params such as "marginMode": "cross" depending on BingX settings.
    }

    try:
        order = exchange.create_order(
            symbol=config.PAIR,
            type="market",
            side=side,
            amount=amount,
            price=None,
            params=params,
        )
    except Exception as e:
        return {
            "ok": False,
            "message": f"❌ LIVE TRADE ERROR: {e}"
        }

    msg = (
        f"✅ LIVE TRADE EXECUTED on BingX\n"
        f"Pair: {config.PAIR}\n"
        f"Side: {signal['side']}\n"
        f"Amount: {amount}\n"
        f"Entry (approx): {entry_price:.4f}\n"
        f"TP: {tp:.4f}\n"
        f"SL: {sl:.4f}\n"
        f"Leverage: {config.LEVERAGE}x\n"
        f"Balance used: ~{balance_usdt * (config.MAX_CAPITAL_PCT / 100):.2f} USDT\n"
        f"(Remaining balance may differ due to exchange rules.)"
    )

    return {
        "ok": True,
        "message": msg,
        "order": order,
    }
