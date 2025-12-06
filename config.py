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
#  BINGX FUTURES API KEYS
# =====================================================

BINGX_API_KEY = os.getenv("BINGX_API_KEY", "")
BINGX_API_SECRET = os.getenv("BINGX_API_SECRET", "")


# =====================================================
#  TRADING SETTINGS
# =====================================================

# Default pair to analyze / trade
PAIR = os.getenv("PAIR", "BTC/USDT")

# Max leverage we allow in futures mode
LEVERAGE = int(os.getenv("LEVERAGE", "2"))

# Maximum capital % used per trade (live mode only)
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "10"))  # keep small at start


# =====================================================
#  LIVE TRADING SWITCH
# =====================================================

# 0 = signals only, 1 = actually send orders to BingX
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"


# =====================================================
#  INTERNAL RUNTIME FLAGS (DON'T TOUCH)
# =====================================================

GRID_ACTIVE = False
