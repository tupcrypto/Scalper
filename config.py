import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSWORD = os.getenv("API_PASSWORD")

# Temporary placeholder — will correct after /list works
SYMBOLS = [
    "BTC-USDT",
    "SUI-USDT"
]

GRID_INTERVAL = 10  # seconds between grid checks
