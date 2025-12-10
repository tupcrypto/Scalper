import os

# ================================
#  TELEGRAM BOT SETTINGS
# ================================
# These come from your Render environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")  # optional, bot can still reply without it


# ================================
#  BITGET API KEYS (USDT FUTURES)
# ================================
# Make sure these match your Bitget API key exactly
BITGET_API_KEY       = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET    = os.getenv("BITGET_API_SECRET", "")
BITGET_PASSPHRASE    = os.getenv("BITGET_PASSPHRASE", "")  # Bitget "password" / passphrase field


# ================================
#  TRADING PAIRS (MUST BE FUTURES FORMAT)
# ================================
# IMPORTANT:
# Use Bitget USDT-M futures symbols in CCXT format:  "SYMBOL/USDT:USDT"
# Example: BTC/USDT:USDT, SUI/USDT:USDT
#
# You can change PAIRS in env as a comma-separated list, e.g.:
# PAIRS="BTC/USDT:USDT,SUI/USDT:USDT"
default_pairs = "BTC/USDT:USDT,SUI/USDT:USDT"
PAIRS = os.getenv("PAIRS", default_pairs).split(",")


# ================================
#  RISK / ALLOCATION SETTINGS
# ================================
# Leverage used on Bitget futures (2x is a good starting point)
LEVERAGE = int(os.getenv("LEVERAGE", "2"))

# Max percentage of your **total USDT futures balance** that the bot is allowed to use.
# Example: 25 → bot can use up to 25% of your balance for all active grids combined
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25"))

# Optional: % of allocated capital per signal (used inside grid_engine if you want)
RISK_PER_TRADE_PCT = float(os.getenv("RISK_PER_TRADE_PCT", "4"))


# ================================
#  MINIMUM ORDER SIZE PER PAIR
# ================================
# You told me Bitget min order is about:
#   - BTC:  ~9.5 USDT
#   - SUI:  ~5.5 USDT
#
# We’ll round up slightly for safety:
MIN_ORDER_USDT = {
    "BTC/USDT:USDT": float(os.getenv("MIN_ORDER_BTC_USDT", "10")),  # safe min for BTC
    "SUI/USDT:USDT": float(os.getenv("MIN_ORDER_SUI_USDT", "6")),   # safe min for SUI
}


# ================================
#  LIVE TRADING SWITCH
# ================================
# LIVE_TRADING = "1"  → real orders
# LIVE_TRADING = "0"  → simulation only (no orders sent)
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"
