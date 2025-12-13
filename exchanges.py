import ccxt
import config

def get_exchange():
    ex = ccxt.bitunix({
        "apiKey": config.API_KEY,
        "secret": config.API_SECRET,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",
        }
    })
    return ex

