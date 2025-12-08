import math
import ccxt
import config


# =====================================================
# CREATE BITGET CLIENT
# =====================================================

def get_exchange():
    try:
        exchange = ccxt.bitget({
            "apiKey": config.EXCHANGE_API_KEY,
            "secret": config.EXCHANGE_API_SECRET,
            "password": config.EXCHANGE_PASSPHRASE,
            "enableRateLimit": True,
            "options": {
                "defaultType": "swap",  # USDT perpetual futures
            },
        })
        return exchange
    except Exception as e:
        raise RuntimeError(f"❌ BITGET INIT ERROR: {e}")


# =====================================================
# UNIVERSAL BITGET FUTURES BALANCE FETCH
# =====================================================

def get_usdt_balance(exchange):
    """
    Correct handling of Bitget futures balance.
    Works on:
    - classic futures
    - unified accounts
    - cross margin
    - isolated margin
    - USDT-M perpetual
    """

    try:
        # Fetch futures balance
        bal = exchange.fetch_balance({"type": "swap"})

        # 1) Try direct total USDT balance (new CCXT format)
        if "total" in bal and isinstance(bal["total"], dict):
            if "USDT" in bal["total"]:
                return float(bal["total"]["USDT"])

        # 2) Try Bitget-style key like "USDT:USDT"
        for k, v in bal.items():
            if isinstance(v, dict) and "USDT" in k:
                if "total" in v:
                    return float(v["total"])
                if "free" in v:
                    return float(v["free"])

        # 3) Try raw info structure (most accurate)
        if "info" in bal:
            info = bal["info"]

            # unified account structure
            if isinstance(info, dict):
                # total equity in USDT futures
                if "totalEquity" in info:
                    return float(info["totalEquity"])

                # USDT equity field
                if "usdtEquity" in info:
                    return float(info["usdtEquity"])

                # nested contract account
                if "data" in info and isinstance(info["data"], dict):
                    data = info["data"]

                    if "usdtEquity" in data:
                        return float(data["usdtEquity"])
                    if "totalEquity" in data:
                        return float(data["totalEquity"])

        # 4) Last fallback — zero
        return 0.0

    except Exception as e:
        print("BALANCE ERROR:", e)
        return 0.0


# =====================================================
# PRICE FETCH
# =====================================================

def get_price(exchange, pair: str):
    try:
        ticker = exchange.fetch_ticker(pair)
        return float(ticker["last"])
    except Exception as e:
        print(f"PRICE ERROR for {pair}:", e)
        return 0.0


# =====================================================
# GRID AMOUNT CALC PER LEVEL
# =====================================================

def calc_amount_per_level(center_price: float, balance_usdt: float) -> float:
    if center_price <= 0 or balance_usdt <= 0:
        return 0.0

    total_capital = balance_usdt * (config.MAX_CAPITAL_PCT / 100.0)
    if total_capital <= 0:
        return 0.0

    capital_per_level = total_capital / config.GRID_LEVELS
    notional = capital_per_level * config.LEVERAGE
    amount = notional / center_price

    # small rounding for safety
    amount = math.floor(amount * 10000) / 10000
    return amount


# =====================================================
# OPEN POSITION
# =====================================================

def open_position(exchange, pair: str, side: str, amount: float):
    if amount <= 0:
        return "⚠️ SKIPPED OPEN: amount <= 0"

    ccxt_side = "buy" if side == "LONG" else "sell"

    try:
        order = exchange.create_order(
            symbol=pair,
            type="market",
            side=ccxt_side,
            amount=amount,
            price=None,
            params={"reduceOnly": False}
        )
        return f"✅ OPEN {side} {pair} amt={amount}"
    except Exception as e:
        return f"❌ OPEN ERROR: {e}"


# =====================================================
# CLOSE POSITION
# =====================================================

def close_position(exchange, pair: str, side: str, amount: float):
    if amount <= 0:
        return "⚠️ SKIPPED CLOSE: amount <= 0"

    opposite_side = "sell" if side == "LONG" else "buy"

    try:
        order = exchange.create_order(
            symbol=pair,
            type="market",
            side=opposite_side,
            amount=amount,
            price=None,
            params={"reduceOnly": True}
        )
        return f"✅ CLOSE {side} {pair} amt={amount}"
    except Exception as e:
        return f"❌ CLOSE ERROR: {e}"

