import ccxt
import config


def get_exchange():
    return ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_API_PASSWORD,   # REQUIRED by Bitget
        "options": {
            "defaultType": "swap",                # for perpetual futures
            "defaultProductType": "USDT-FUTURES"  # THIS FIXES THE PERMISSION ISSUE
        }
    })


def get_price(exchange, pair):
    ticker = exchange.fetch_ticker(pair)
    return ticker["last"]


def get_usdt_balance(exchange):
    # This will be fixed AFTER we see RAW OBJECT
    # For now return total equity or 0
    raw = exchange.fetch_balance({"productType": "USDT-FUTURES"})

    # TRY VARIANTS SAFELY (temporary)
    try:
        if "USDT" in raw and "total" in raw["USDT"]:
            return raw["USDT"]["total"]
    except:
        pass

    try:
        if "total" in raw and "USDT" in raw["total"]:
            return raw["total"]["USDT"]
    except:
        pass

    return 0

