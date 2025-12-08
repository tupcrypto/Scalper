# =========================
# config.py  (FULL FILE)
# =========================

import os

# =========================
# TELEGRAM
# =========================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# =========================
# BITGET CREDENTIALS
# =========================
BITGET_API_KEY       = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET    = os.getenv("BITGET_API_SECRET", "")
BITGET_PASSPHRASE    = os.getenv("BITGET_PASSPHRASE", "")

# =========================
# TRADING SETTINGS
# =========================
PAIRS = ["BTC/USDT", "SUI/USDT"]      # you can add more

MAX_CAPITAL_PCT = 100                 # max allocation in %
GRID_LEVELS = 14
GRID_RANGE_PCT = 0.0065               # 0.65%

