# =========================
# config.py  (FINAL)
# =========================
import os

# ---------- TELEGRAM ----------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# can be string; PTB accepts both, but we’ll keep it as string
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------- BITGET API ----------
BITGET_API_KEY        = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET     = os.getenv("BITGET_API_SECRET", "")
BITGET_PASSPHRASE     = os.getenv("BITGET_PASSPHRASE", "")  # this was missing

# ---------- TRADING SETTINGS ----------
# Comma-separated list, e.g. "BTC/USDT,SUI/USDT"
PAIRS_ENV = os.getenv("PAIRS", "BTC/USDT,SUI/USDT")
PAIRS = [p.strip() for p in PAIRS_ENV.split(",") if p.strip()]

# % of balance to use per scan (for order sizing)
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "100"))

# Aggressive grid or not
AGGRESSIVE = os.getenv("AGGRESSIVE", "1") == "1"

# Live mode – if 0, only sends signals, no real orders
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

