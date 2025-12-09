# =========================
# config.py  (GRID BOT)
# =========================
import os

# ---------- TELEGRAM ----------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")  # your personal chat id

# ---------- BITGET API ----------
BITGET_API_KEY        = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET     = os.getenv("BITGET_API_SECRET", "")
BITGET_PASSPHRASE     = os.getenv("BITGET_PASSPHRASE", "")

# ---------- TRADING SETTINGS ----------
# e.g. "BTC/USDT,SUI/USDT"
PAIRS_ENV = os.getenv("PAIRS", "BTC/USDT,SUI/USDT")
PAIRS = [p.strip() for p in PAIRS_ENV.split(",") if p.strip()]

# Your assumed futures balance
ASSUMED_BALANCE_USDT = float(os.getenv("ASSUMED_BALANCE_USDT", "52"))

# Maximum exposure % per grid trade cycle
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "50"))

# Grid step %
# 0.0015 = 0.15% band width
GRID_STEP_PCT = float(os.getenv("GRID_STEP_PCT", "0.0015"))

# If 1 → real orders, if 0 → paper simulation
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

