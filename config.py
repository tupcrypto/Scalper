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

# Comma-separated list of pairs, e.g. "BTC/USDT,SUI/USDT"
PAIRS_STR = os.getenv("PAIRS", "BTC/USDT,SUI/USDT")
PAIRS = [p.strip() for p in PAIRS_STR.split(",") if p.strip()]

# Main display pair
PAIR = PAIRS[0] if PAIRS else "BTC/USDT"

LEVERAGE = int(os.getenv("LEVERAGE", "2"))                 # leverage used
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "20"))  # total % of account allocated to grid

# Grid parameters (Mode B: moderately aggressive)
GRID_LEVELS = int(os.getenv("GRID_LEVELS", "14"))         # number of grid levels
GRID_RANGE_PCT = float(os.getenv("GRID_RANGE_PCT", "0.025"))  # ±2.5% band around center price


# =====================================================
#  LIVE TRADING SWITCH
# =====================================================

# 0 = signals only (no orders), 1 = real orders on BingX
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"


# =====================================================
#  INTERNAL RUNTIME FLAGS (DON'T TOUCH)
# =====================================================

GRID_ACTIVE = False
