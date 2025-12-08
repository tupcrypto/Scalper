import math
import ccxt
import config
import os

# LOAD EXCHANGE KEYS
API_KEY     = config.EXCHANGE_API_KEY
API_SECRET  = config.EXCHANGE_API_SECRET
PASSPHRASE  = config.EXCHANGE_PASSPHRASE   # required by Bitget


# =====================================================
# CREATE BITGET CLIENT
# =====================================================

def get_exchange():
    try:
        exchange = ccxt.bitget({
            "apiKey": API_KEY,
            "secret": API_SECRET,
            "password": PASSPHRASE,
            "enableRateLimit": True,
            "options": {
                "defaultType": "swap",  # USDT perpetual futures
            },
        })
        return exchange
    except Exception as e:
        raise RuntimeError(f"❌ BITGET INIT ERROR: {e}")


# =====================================================
# BALANCE FETCH
# =====================================================

def get_usdt_balance(exchange):
    try:
        balance = exchange.fetch_balance()
        usdt = balance.get("USDT", {})
        free = usdt.get("free", 0.0)
        total = usdt.get("total", free)
        return float(total or free or 0.0)
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
# GRID SIZE CALC
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

    amount = math.floor(amount * 10000) / 10000
    return amount


# =====================================================
# ORDER EXECUTION
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

