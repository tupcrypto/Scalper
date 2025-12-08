import os

# ---------------------------
# TELEGRAM BOT SETTINGS
# ---------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------
# BITGET EXCHANGE KEYS
# ---------------------------
BITGET_API_KEY      = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET   = os.getenv("BITGET_API_SECRET", "")
BITGET_API_PASSWORD = os.getenv("BITGET_API_PASSWORD", "")  # Bitget passphrase

# ---------------------------
# TRADING SETTINGS
# ---------------------------
PAIRS = ["BTC/USDT", "SUI/USDT"]

LEVERAGE        = int(os.getenv("LEVERAGE", "2"))
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25"))

GRID_LEVELS     = 14
GRID_RANGE_PCT  = 0.0065

# Live trading mode flag
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

# Runtime flag used by auto_loop
GRID_ACTIVE = False
