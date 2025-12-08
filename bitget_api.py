import ccxt
import config


def get_exchange():
    """
    Bitget futures exchange (only used for placing orders when LIVE_TRADING=1
    and for fetching prices).
    """
    return ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_API_PASSWORD,
        "options": {
            "defaultType": "swap",   # USDT-M perpetual futures
        },
    })


def get_price(symbol: str) -> float:
    """
    Fetch last traded price for a futures symbol.
    """
    ex = get_exchange()
    ticker = ex.fetch_ticker(symbol)
    return ticker["last"]

