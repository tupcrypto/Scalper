import ccxt
import config

def get_exchange():
    return ccxt.bitget({
        "apiKey":    config.BITGET_API_KEY,
        "secret":    config.BITGET_API_SECRET,
        "password":  config.BITGET_API_PASSWORD,
        "options": {
            "defaultType": "swap",
        }
    })


# ---- NEW: simulated balance mode ----
# we do NOT query Bitget, we assume user configured capital
#
def get_futures_balance():
    try:
        # use MAX_CAPITAL_PCT dynamically but scale 100%
        # or let user set STATIC_BALANCE
        return float(config.ASSUMED_BALANCE_USDT)
    except:
        return 0


def get_price(symbol):
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(symbol)
    return ticker["last"]

