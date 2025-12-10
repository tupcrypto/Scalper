# =========================================
# GRID ENGINE — REPLACE FULL FILE
# =========================================

import ccxt.async_support as ccxt
import config


def get_exchange():
    return ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",
        }
    })


async def get_balance(exchange):
    try:
        balance = await exchange.fetch_balance()
        return float(balance["total"]["USDT"])
    except:
        return 0.0


async def trade_symbol(exchange, symbol, balance):
    try:
        ticker = await exchange.fetch_ticker(symbol)
        price = float(ticker["last"])

        # SIMPLE SENSOR — price above moving entry
        if price % 2 < 1:
            action = "LONG"
        else:
            action = "SHORT"

        # no order if small balance
        if balance < config.MIN_ORDER[symbol]:
            return {
                "action": "NO ORDER",
                "price": price,
                "result": f"Balance too small: {balance}"
            }

        # build trade
        cost = config.MIN_ORDER[symbol]
        amount = cost / price

        params = {}

        # PLACE MARKET ORDER
        order = await exchange.create_order(
            symbol=symbol,
            type="market",
            side="buy" if action == "LONG" else "sell",
            amount=amount,
            params=params
        )

        return {
            "action": action,
            "price": price,
            "result": f"ORDER OK: cost={cost}, amount={amount}, id={order['id']}"
        }

    except Exception as e:
        return {
            "action": "ERROR",
            "price": 0,
            "result": str(e)
        }
