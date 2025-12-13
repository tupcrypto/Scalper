# config.py
import os

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Exchange selection (ccxt id). e.g. "bitget", "blofin", "toobit", "bingx"
# MUST match a ccxt exchange id available in environment (see logs)
EXCHANGE_ID = os.getenv("EXCHANGE_ID", "blofin").strip()

# Exchange credentials
API_KEY = os.getenv("API_KEY", "").strip()
API_SECRET = os.getenv("API_SECRET", "").strip()
API_PASSWORD = os.getenv("API_PASSWORD", "").strip()  # some exchanges require 'password' or 'passphrase'

# Symbols to trade (user-friendly) — we'll test existence with /list
SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", "BTCUSDT,SUIUSDT").split(",") if s.strip()]

# Grid / scan settings
GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "10"))
MIN_ORDER_USDT = float(os.getenv("MIN_ORDER_USDT", "5.5"))  # default minimum
