# config.py  (FULL replacement)
import os
import json

# ---------------------------
# TELEGRAM
# ---------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------
# BITGET KEYS (Classic / USDT-M Futures)
# ---------------------------
BITGET_API_KEY = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET = os.getenv("BITGET_API_SECRET", "")
BITGET_PASSPHRASE = os.getenv("BITGET_PASSPHRASE", "")

# ---------------------------
# PAIRS (user-friendly format). We'll normalize to Bitget futures symbol internally.
# Examples: "BTC/USDT", "SUI/USDT"
# You may set PAIRS_JSON env like '["BTC/USDT","SUI/USDT"]'
# ---------------------------
PAIRS = json.loads(os.getenv("PAIRS_JSON", '["BTC/USDT","SUI/USDT"]'))

# ---------------------------
# Trading / allocation
# ---------------------------
LEVERAGE = int(os.getenv("LEVERAGE", "2"))
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25.0"))  # percent of futures balance allowed to use across all grids
GRID_LEVELS = int(os.getenv("GRID_LEVELS", "14"))
GRID_RANGE_PCT = float(os.getenv("GRID_RANGE_PCT", "0.0065"))  # 0.65% default per side
GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "30"))

# ---------------------------
# Minimum order sizes (USDT). Default safe values; override via MIN_ORDER_OVERRIDES_JSON
# ---------------------------
MIN_ORDER = float(os.getenv("MIN_ORDER", "5.5"))
MIN_ORDER_OVERRIDES = {}
_min_json = os.getenv("MIN_ORDER_OVERRIDES_JSON", "")
if _min_json:
    try:
        MIN_ORDER_OVERRIDES = json.loads(_min_json)
    except Exception:
        MIN_ORDER_OVERRIDES = {}

def get_min_order_for_pair(pair: str) -> float:
    # pair is like "BTC/USDT" or "SUI/USDT"
    if pair in MIN_ORDER_OVERRIDES:
        try:
            return float(MIN_ORDER_OVERRIDES[pair])
        except:
            pass
    return float(MIN_ORDER)

# ---------------------------
# Live trading flag (safety)
# ---------------------------
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"   # set to "1" to allow real order placement

# ---------------------------
# Debug/version
# ---------------------------
DEBUG = os.getenv("DEBUG", "1") == "1"
CONFIG_VERSION = "bitget-final-v1"

if DEBUG:
    print("===== CONFIG LOADED =====")
    print("PAIRS:", PAIRS)
    print("LEVERAGE:", LEVERAGE)
    print("MAX_CAPITAL_PCT:", MAX_CAPITAL_PCT)
    print("GRID_LEVELS:", GRID_LEVELS)
    print("GRID_RANGE_PCT:", GRID_RANGE_PCT)
    print("GRID_LOOP_SECONDS:", GRID_LOOP_SECONDS)
    print("MIN_ORDER (default):", MIN_ORDER)
    print("MIN_ORDER_OVERRIDES:", MIN_ORDER_OVERRIDES)
    print("LIVE_TRADING:", LIVE_TRADING)
    print("CONFIG_VERSION:", CONFIG_VERSION)
    print("=========================")
