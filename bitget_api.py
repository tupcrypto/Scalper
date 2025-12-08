import ccxt
import config
import json


def get_exchange():
    return ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_API_PASSWORD,
        "options": {
            "defaultType": "swap",     # futures mode
        }
    })


def get_futures_balance():
    try:
        exchange = get_exchange()

        # MUST load markets before private endpoints
        exchange.load_markets()

        # Bitget REAL endpoint for unified futures margin
        raw = exchange.privateMixGetAccountAccounts()
        # raw is dict like:
        # { "code": "00000", "msg": "success", "data": [ {...} ] }

        if raw.get("code") != "00000":
            return f"RAW BALANCE ERROR: {json.dumps(raw)}"

        data = raw.get("data", [])
        if not data:
            return 0

        # unified margin account returns balance under 'usdtEquity'
        acct = data[0]
        balance = float(acct.get("usdtEquity", 0))

        return balance

    except Exception as e:
        return f"RAW BALANCE ERROR: {str(e)}"


def get_price(symbol):
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(symbol)
    return ticker["last"]

