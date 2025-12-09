# =========================
# config.py  (FINAL SIMPLE)
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

# ⚠️ We stop fighting Bitget’s balance format.
#    You tell the bot your balance manually here:
ASSUMED_BALANCE_USDT = float(os.getenv("ASSUMED_BALANCE_USDT", "50"))

# % of balance to use for trading (total exposure)
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "100"))

# Aggressive band behaviour
AGGRESSIVE = os.getenv("AGGRESSIVE", "1") == "1"

# Live mode – if 0, only signals, no real orders
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

