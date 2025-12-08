import ccxt
import config
import json

def get_exchange():
    return ccxt.bitget({
        "apiKey":    config.BITGET_API_KEY,
        "secret":    config.BITGET_API_SECRET,
        "password":  config.BITGET_API_PASSWORD,
        "options": {
            "defaultType": "swap",   # USDT-M futures
        }
    })


def get_futures_balance():
    try:
        exchange = get_exchange()
        exchange.load_markets()

        # REAL working endpoint for USDT-M futures balance
        #
        # RETURN FORMAT:
        # {
        #   "code": "00000",
        #   "msg": "success",
        #   "data": [
        #       { "marginCoin": "USDT", "available": "52.105", ... }
        #   ]
        # }
        #
        raw = exchange.privateMixGetAccountBalance()

        if raw.get("code") != "00000":
            return f"RAW BALANCE ERROR: {json.dumps(raw)}"

        balances = raw.get("data", [])
        if not balances:
            return 0

        # pick USDT futures wallet
        for b in balances:
            if b.get("marginCoin") == "USDT":
                return float(b.get("available", 0))

        return 0

    except Exception as e:
        return f"RAW BALANCE ERROR: {str(e)}"


def get_price(symbol):
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(symbol)
    return ticker["last"]
