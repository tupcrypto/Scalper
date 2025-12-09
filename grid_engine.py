# ======================================================
# grid_engine.py — FINAL CLEAN + SAFE VERSION
# ======================================================

import ccxt
import config

GRID_CENTER = {}


def get_exchange():
    try:
        ex = ccxt.bitget({
            "apiKey": config.BITGET_API_KEY,
            "secret": config.BITGET_API_SECRET,
            "password": config.BITGET_PASSPHRASE,
            "enableRateLimit": True,
            "options": {
                "defaultType": "swap",
                "createMarketBuyOrderRequiresPrice": False,
            },
        })
        ex.load_markets()
        return ex
    except Exception as e:
        print("EXCHANGE INIT ERROR: " + str(e))
        return None


def get_balance():
    try:
        return float(config.ASSUMED_BALANCE_USDT)
    except:
        return 0.0


def get_price(exchange, symbol):
    try:
        t = exchange.fetch_ticker(symbol)
        return float(t["last"])
    except Exception as e:
        print("PRICE ERROR " + symbol + ": " + str(e))
        return 0.0


def check_grid_signal(symbol, price, balance):
    if price <= 0:
        return "NO DATA"
    if balance <= 0:
        return "NO BALANCE"

    step = float(config.GRID_STEP_PCT)

    if symbol not in GRID_CENTER:
        GRID_CENTER[symbol] = price
        return "INIT GRID — HOLD"

    center = GRID_CENTER[symbol]
    upper = center * (1 + step)
    lower = center * (1 - step)

    if price >= upper:
        GRID_CENTER[symbol] = price
        return "SHORT_ENTRY @ " + str(price)

    if price <= lower:
        GRID_CENTER[symbol] = price
        return "LONG_ENTRY @ " + str(price)

    return "HOLD — Neutral zone"


def execute_order(exchange, symbol, signal, balance):
    if "ENTRY" not in signal:
        return "NO ORDER"

    if not config.LIVE_TRADING:
        return "[SIMULATION] EXECUTED " + signal + " " + symbol

    price = get_price(exchange, symbol)
    if price <= 0:
        return "BAD PRICE"

    if symbol.startswith("SUI"):
        min_cost_usdt = 5.5
    elif symbol.startswith("BTC"):
        min_cost_usdt = 9.5
    else:
        min_cost_usdt = 10.0

    cost_param = str(min_cost_usdt)

    try:
        exchange.set_leverage(
            leverage=5,
            symbol=symbol,
            params={"marginCoin": "USDT"},
        )
    except:
        pass

    try:
        exchange.set_margin_mode(
            marginMode="isolated",
            symbol=symbol,
            params={"marginCoin": "USDT"},
        )
    except:
        pass

    try:
        side = "buy"
        if "SHORT_ENTRY" in signal:
            side = "sell"

        order = exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=None,
            price=None,
            params={
                "marginCoin": "USDT",
                "cost": cost_param,
                "force": "normal",
            },
        )

        return "ORDER OK: symbol=" + symbol + ", cost=" + cost_param + ", order=" + str(order)

    except Exception as e:
        return "ORDER ERROR: " + str(e)
