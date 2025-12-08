# =========================
# config.py  (FULL FILE)
# =========================

import os

# -------------------------
# TELEGRAM SETTINGS
# -------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")  # optional push target

# -------------------------
# BITGET API KEYS
# -------------------------
BITGET_API_KEY        = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET     = os.getenv("BITGET_API_SECRET", "")
BITGET_API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE", "")

# -------------------------
# TRADING SETTINGS
# -------------------------
# Comma-separated list, e.g. "BTC/USDT,SUI/USDT"
PAIRS_ENV = os.getenv("PAIRS", "BTC/USDT,SUI/USDT")
PAIRS = [p.strip() for p in PAIRS_ENV.split(",") if p.strip()]

MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "100"))   # % of futures balance to use
GRID_LEVELS     = int(os.getenv("GRID_LEVELS", "14"))          # grid steps
GRID_RANGE_PCT  = float(os.getenv("GRID_RANGE_PCT", "0.0065")) # 0.65% band

# Live trading flag: 1 = real orders, 0 = signals only
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"
