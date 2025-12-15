import requests
from config import MEXC_BASE_URL

def get_futures_symbols():
    url = f"{MEXC_BASE_URL}/api/v1/contract/detail"
    r = requests.get(url, timeout=10).json()
    return [
        s["symbol"]
        for s in r["data"]
        if s["quoteCoin"] == "USDT" and s["volume"] >= 40_000_000
    ]

def get_price(symbol):
    url = f"{MEXC_BASE_URL}/api/v1/contract/index_price/{symbol}"
    r = requests.get(url, timeout=10).json()
    return float(r["data"]["indexPrice"])
