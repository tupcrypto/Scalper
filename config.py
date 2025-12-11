# ============================
# config.py  (FULL REPLACEMENT)
# ============================

import os
import json


# ---------------------------
# TELEGRAM SETTINGS
# ---------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ---------------------------
# BITGET API KEYS (FUTURES)
# ---------------------------
BITGET_API_KEY = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET = os.getenv("BITGET_API_SECRET", "")
BITGET_PASSPHRASE = os.getenv("BITGET_PASSPHRASE", "")


# ---------------------------
# TRADING PAIRS
# ---------------------------
PAIRS = json.loads(os.getenv("PAIRS_JSON", '["BTC/USDT", "SUI/USDT"]'))


# ---------------------------
# GRID SETTINGS
# ---------------------------
LEVERAGE = int(os.getenv("LEVERAGE", "2"))
GRID_LEVELS = int(os.getenv("GRID_LEVELS", "14"))
GRID_RANGE_PCT = float(os.getenv("GRID_RANGE_PCT", "0.0065"))
GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "10"))  # loop every 10s
GRID_MODE = os.getenv("GRID_MODE", "neutral").lower()


# ---------------------------
# CAPITAL SETTINGS
# ---------------------------
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25"))


# ---------------------------
# MINIMUM ORDER SYSTEM
# ---------------------------
# Global fallback minimum order requirement
MIN_ORDER = float(os.getenv("MIN_ORDER", "5.5"))

# Per-pair overrides provided by the user
MIN_ORDER_OVERRIDES = {}

_min_json = os.getenv("MIN_ORDER_OVERRIDES_JSON", "")
if _min_json:
    try:
        MIN_ORDER_OVERRIDES = json.loads(_min_json)
    except Exception:
        MIN_ORDER_OVERRIDES = {}


def get_min_order_for_pair(pair: str) -> float:
    """Return min order in USDT for the specific pair."""
    try:
        if pair in MIN_ORDER_OVERRIDES:
            return float(MIN_ORDER_OVERRIDES[pair])
    except:
        pass

    return float(MIN_ORDER)


# ---------------------------
# SAFETY SETTINGS
# ---------------------------
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"
QUOTE_CURRENCY = "USDT"
DEBUG = os.getenv("DEBUG", "1") == "1"

GRID_ACTIVE = False


# ---------------------------
# DEBUG PRINT (appears in Render logs)
# ---------------------------
if DEBUG:
    print("=============== CONFIG LOADED ===============")
    print("PAIRS:", PAIRS)
    print("LEVERAGE:", LEVERAGE)
    print("GRID_LOOP_SECONDS:", GRID_LOOP_SECONDS)
    print("MIN_ORDER:", MIN_ORDER)
    print("MIN_ORDER_OVERRIDES:", MIN_ORDER_OVERRIDES)
    print("============================================")
    print("CONFIG_VERSION = v14.12.1")  # do NOT remove — used to verify on Render
