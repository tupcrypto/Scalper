import os

# ---------------------------
# TELEGRAM BOT SETTINGS
# ---------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------
# EXCHANGE KEYS (BITGET)
# ---------------------------
EXCHANGE_API_KEY    = os.getenv("EXCHANGE_API_KEY", "")
EXCHANGE_API_SECRET = os.getenv("EXCHANGE_API_SECRET", "")
EXCHANGE_PASSPHRASE = os.getenv("EXCHANGE_PASSPHRASE", "")  # Bitget uses passphrase

# ---------------------------
# TRADING SETTINGS
# ---------------------------
PAIRS = ["BTC/USDT", "SUI/USDT"]    # add more if needed

LEVERAGE = int(os.getenv("LEVERAGE", "2"))
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25"))  # total allocation

GRID_LEVELS = 14               # number of grid units
GRID_RANGE_PCT = 0.0065        # 0.65% above/below center (adjustable)

# LIVE MODE (IMPORTANT)
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

