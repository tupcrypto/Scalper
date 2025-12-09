# =========================
# config.py (CLEAN)
# =========================
import os

# ---------- TELEGRAM ----------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------- BITGET API ----------
BITGET_API_KEY        = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET     = os.getenv("BITGET_API_SECRET", "")
BITGET_PASSPHRASE     = os.getenv("BITGET_PASSPHRASE", "")

# ---------- TRADING SETTINGS ----------
# Example: "BTC/USDT,SUI/USDT"
PAIRS_ENV = os.getenv("PAIRS", "BTC/USDT,SUI/USDT")
PAIRS = [p.strip() for p in PAIRS_ENV.split(",") if p.strip()]

# Your futures balance (we use this for sizing to avoid Bitget balance headaches)
ASSUMED_BALANCE_USDT = float(os.getenv("ASSUMED_BALANCE_USDT", "52"))

# Max % of balance allocated across all pairs
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "50"))  # e.g. 50% of 52 USDT

# Grid step in % (0.0015 = 0.15%)
GRID_STEP_PCT = float(os.getenv("GRID_STEP_PCT", "0.0015"))

# 1 = real trades, 0 = only simulate
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"
