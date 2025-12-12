import ccxt.async_support as ccxt

async def get_exchange():
    exchange = ccxt.blofin({
        "apiKey": os.getenv("API_KEY"),
        "secret": os.getenv("API_SECRET"),
        "password": os.getenv("API_PASSWORD"),
        "options": {
            "defaultType": "swap"
        }
    })
    await exchange.load_markets()
    return exchange
