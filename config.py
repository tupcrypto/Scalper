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
# Comma-separated list, e.g. "BTC/USDT,SUI/USDT"
PAIRS_ENV = os.getenv("PAIRS", "BTC/USDT,SUI/USDT")
PAIRS = [p.strip() for p in PAIRS_ENV.split(",") if p.strip()]

# We use your assumed balance instead of the Bitget balance API
ASSUMED_BALANCE_USDT = float(os.getenv("ASSUMED_BALANCE_USDT", "52"))

# Max percentage of that balance the bot is allowed to use
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "50"))  # e.g. 50% of 52

# Grid step in percent (e.g. 0.15% = 0.0015)
GRID_STEP_PCT = float(os.getenv("GRID_STEP_PCT", "0.0015"))  # 0.15%

# Live mode – if 0, only signals, no real orders
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

# For logging text: "AGGRESSIVE" or not
AGGRESSIVE = True  # just a label now

