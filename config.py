import os

# ---------------------------
# TELEGRAM BOT SETTINGS
# ---------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------
# BITGET KEYS (IMPORTANT)
# ---------------------------
EXCHANGE_API_KEY    = os.getenv("EXCHANGE_API_KEY", "")
EXCHANGE_API_SECRET = os.getenv("EXCHANGE_API_SECRET", "")
EXCHANGE_PASSPHRASE = os.getenv("EXCHANGE_PASSPHRASE", "")

# ---------------------------
# TRADING SETTINGS
# ---------------------------
PAIRS = ["BTC/USDT", "SUI/USDT"]      # both long & short possible
GRID_LEVELS = 14                      # more grids = more trades
GRID_RANGE_PCT = 0.0065               # aggressive grid range (0.65%)

MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "100"))
LEVERAGE = int(os.getenv("LEVERAGE", "2"))

# Set this to 1 to enable REAL trading
LIVE_TRADING = os.getenv("LIVE_TRADING", "1") == "1"
