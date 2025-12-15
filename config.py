import os

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Analysis rules
MIN_PROBABILITY = 75  # minimum % to give a trade
VOLUME_FILTER = 40_000_000  # $40M

# Timeframes
TIMEFRAMES = ["15m", "1h"]

# MEXC
MEXC_BASE_URL = "https://contract.mexc.com"
