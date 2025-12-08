import ccxt
import config


def get_exchange():
    return ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_API_PASSWORD,
        "options": {
            "defaultType": "swap",       # VERY IMPORTANT – this tells Bitget we want futures
        }
    })


def get_futures_balance():
    try:
        exchange = get_exchange()
        balance = exchange.fetch_balance()
        # Unified futures balance is in 'USDT'
        usdt = balance.get("USDT", {})
        free = float(usdt.get("free", 0))
        return free
    except Exception as e:
        return f"RAW FUTURES BALANCE ERROR: {str(e)}"


def get_price(symbol):
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']
