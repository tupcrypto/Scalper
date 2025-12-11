import os

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")  # numeric chat id or your user id

# Toobit (set these as Render env vars)
TOOBIT_API_KEY = os.getenv("TOOBIT_API_KEY", "")
TOOBIT_API_SECRET = os.getenv("TOOBIT_API_SECRET", "")

# Trading
PAIRS = os.getenv("PAIRS", "BTC/USDT,SUI/USDT").split(",")   # comma separated
LEVERAGE = int(os.getenv("LEVERAGE", "3"))
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25"))   # percent of balance to use total
MIN_ORDER_USDT = float(os.getenv("MIN_ORDER_USDT", "6.0"))    # minimum allowed order cost in USDT per exchange
GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "30"))
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

# Bot behavior
MODE = os.getenv("MODE", "PI_ONEX")  # just a label
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
