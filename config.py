import os

# =====================================================
#  TELEGRAM CONFIGURATION
# =====================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))  # numeric user ID


# =====================================================
#  BINGX FUTURES API KEYS
# =====================================================

BINGX_API_KEY = os.getenv("BINGX_API_KEY", "")
BINGX_API_SECRET = os.getenv("BINGX_API_SECRET", "")


# =====================================================
#  TRADING SETTINGS
# =====================================================

# Comma-separated list of pairs to scan/trade, e.g. "BTC/USDT,SUI/USDT"
PAIRS_STR = os.getenv("PAIRS", "BTC/USDT,SUI/USDT")
PAIRS = [p.strip() for p in PAIRS_STR.split(",") if p.strip()]

# For backward-compatibility: "main" pair (used e.g. in /status text)
PAIR = PAIRS[0] if PAIRS else "BTC/USDT"

LEVERAGE = int(os.getenv("LEVERAGE", "2"))          # max leverage
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "5"))  # % of balance per trade


# =====================================================
#  LIVE TRADING SWITCH
# =====================================================

# 0 = signals only, 1 = actually send orders to BingX
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"


# =====================================================
#  INTERNAL RUNTIME FLAGS (DON'T TOUCH)
# =====================================================

GRID_ACTIVE = False
