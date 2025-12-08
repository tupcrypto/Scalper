import os

# =====================================================
# TELEGRAM BOT SETTINGS
# =====================================================
# Your Telegram bot token and your personal chat ID
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# =====================================================
# BITGET EXCHANGE API KEYS
# =====================================================
# Make sure these env variables exist in Render:
#   BITGET_API_KEY
#   BITGET_API_SECRET
#   BITGET_API_PASSWORD   (this is the API passphrase)
BITGET_API_KEY      = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET   = os.getenv("BITGET_API_SECRET", "")
BITGET_API_PASSWORD = os.getenv("BITGET_API_PASSWORD", "")

# =====================================================
# TRADING / GRID SETTINGS
# =====================================================
# Futures pairs to use for grid trading
PAIRS = ["BTC/USDT", "SUI/USDT"]   # you can add more later

# Leverage and capital usage
LEVERAGE        = int(os.getenv("LEVERAGE", "2"))
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25"))  # % of (assumed) balance to use

# Grid configuration
GRID_LEVELS    = int(os.getenv("GRID_LEVELS", "14"))          # number of grid levels
GRID_RANGE_PCT = float(os.getenv("GRID_RANGE_PCT", "0.0065")) # 0.65% above/below center

# =====================================================
# ASSUMED BALANCE MODE (NO API BALANCE READ)
# =====================================================
# Because Bitget keeps blocking futures balance API in your region,
# we tell the bot how much USDT to assume is in the futures wallet.
# Set this in Render env as ASSUMED_BALANCE_USDT, or it defaults to 52.
ASSUMED_BALANCE_USDT = float(os.getenv("ASSUMED_BALANCE_USDT", "52"))

# =====================================================
# MODE FLAGS
# =====================================================
# LIVE_TRADING = False  -> signals only, no real orders
# LIVE_TRADING = True   -> place real futures orders on Bitget
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

# Runtime flag toggled by /start and /stop
GRID_ACTIVE = False
