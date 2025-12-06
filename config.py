import os

# =====================================================
#  TELEGRAM CONFIGURATION
# =====================================================

# Telegram bot token (from BotFather)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Numeric Telegram chat ID (MUST come from @userinfobot)
# Example: 123456789
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))


# =====================================================
#  BINGX FUTURES API KEYS (for later execution mode)
# =====================================================

BINGX_API_KEY = os.getenv("BINGX_API_KEY", "")
BINGX_API_SECRET = os.getenv("BINGX_API_SECRET", "")


# =====================================================
#  SCALPING / TRADING SETTINGS
# =====================================================

# Default pair to analyze
PAIR = os.getenv("PAIR", "BTC/USDT")

# Max leverage we will allow in futures mode
# NOTE: In auto mode, bot will not exceed this
LEVERAGE = int(os.getenv("LEVERAGE", "2"))

# Maximum capital % used per trade (live mode only)
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25"))


# =====================================================
#  INTERNAL RUNTIME FLAGS (DON'T TOUCH)
# =====================================================

# Used later when auto trade logic is added
GRID_ACTIVE = False
