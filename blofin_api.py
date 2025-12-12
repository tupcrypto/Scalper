# blofin_api.py
import ccxt.async_support as ccxt
import config

async def get_exchange():
    """Initialize Blofin futures exchange"""
    exchange = ccxt.blofin({
        "apiKey": config.BLOFIN_API_KEY,
        "secret": config.BLOFIN_API_SECRET,
        "password": config.BLOFIN_PASSWORD,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap"
        }
    })

    await exchange.load_markets()
    return exchange
