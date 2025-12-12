# config.py
import os

# Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Blofin credentials
BLOFIN_API_KEY = os.getenv("BLOFIN_API_KEY")
BLOFIN_API_SECRET = os.getenv("BLOFIN_API_SECRET")
BLOFIN_PASSWORD = os.getenv("BLOFIN_PASSWORD")

# Trading pairs (Blofin futures format)
SYMBOLS = ["BTC-USDT-SWAP", "SUI-USDT-SWAP"]

# Grid configuration
MIN_ORDER_USDT = 5.5
GRID_INTERVAL = 0.25
GRID_LOOP_SECONDS = 4

