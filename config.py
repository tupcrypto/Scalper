# config.py
import os

# ---------------------------
# TELEGRAM BOT SETTINGS
# ---------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")  # your personal TG ID (string or int)

# ---------------------------
# BITGET EXCHANGE KEYS (FUTURES)
# ---------------------------
# Use the exact env var names below in Render / environment settings
BITGET_API_KEY = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET = os.getenv("BITGET_API_SECRET", "")
BITGET_PASSPHRASE = os.getenv("BITGET_PASSPHRASE", "")

# ---------------------------
# TRADING SETTINGS
# ---------------------------
PAIRS = ["BTC/USDT", "SUI/USDT"]   # pairs to trade
LEVERAGE = int(os.getenv("LEVERAGE", "2"))
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25"))  # percent of account allocated in total
GRID_LEVELS = int(os.getenv("GRID_LEVELS", "14"))
GRID_RANGE_PCT = float(os.getenv("GRID_RANGE_PCT", "0.0065"))  # 0.65% range above/below center

# safety / runtime
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"   # set to "1" to enable live order placement
GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "120"))  # how often the grid loop runs (seconds)

# Optional: set default currency for allocation calculations
QUOTE_CURRENCY = os.getenv("QUOTE_CURRENCY", "USDT")

# debug toggles
DEBUG = os.getenv("DEBUG", "1") == "1"

# DO NOT EDIT: runtime flag internal use
GRID_ACTIVE = False
