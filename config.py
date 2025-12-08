import os

# ---------------------------
# TELEGRAM BOT SETTINGS
# ---------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------
# BITGET EXCHANGE KEYS
# (MUST MATCH RENDER ENV NAMES)
# ---------------------------
BITGET_API_KEY      = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET   = os.getenv("BITGET_API_SECRET", "")
BITGET_API_PASSWORD = os.getenv("BITGET_API_PASSWORD", "")  # Bitget passphrase

# ---------------------------
# TRADING SETTINGS
# ---------------------------
# Pairs to trade on Bitget USDT-M futures
PAIRS = ["BTC/USDT", "SUI/USDT"]   # you can add more later

# Leverage & capital allocation
LEVERAGE        = int(os.getenv("LEVERAGE", "2"))
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25"))  # % of account to use in grid

# Grid configuration
GRID_LEVELS    = 14          # number of grid levels
GRID_RANGE_PCT = 0.0065      # 0.65% above/below center (you can tune later)

# Live mode: 0 = signals only, 1 = real orders
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

# Runtime flag used by bot.py to control auto_loop
GRID_ACTIVE = False

