# config.py
import os
from decimal import Decimal

# ============= TELEGRAM =================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ============= EXCHANGE =================
EXCHANGE_ID = "blofin"  # fixed

EXCHANGE_API_KEY        = os.getenv("EXCHANGE_API_KEY", "")
EXCHANGE_API_SECRET     = os.getenv("EXCHANGE_API_SECRET", "")
EXCHANGE_API_PASSPHRASE = os.getenv("EXCHANGE_API_PASSPHRASE", "")

# BloFin uses swap markets, so no slash
PAIRS = ["BTCUSDT", "SUIUSDT"]  

QUOTE_ASSET = "USDT"

# Grid settings
ALLOCATION_PER_PAIR = Decimal(os.getenv("ALLOCATION_PER_PAIR", "0.25"))
MIN_ORDER           = Decimal(os.getenv("MIN_ORDER", "6.0"))   # Blofin's min order ~5.5

LEVERAGE = int(os.getenv("LEVERAGE", "1"))
GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "20"))

LIVE_TRADING = os.getenv("LIVE_TRADING", "true").lower() == "true"

VERBOSE = True

