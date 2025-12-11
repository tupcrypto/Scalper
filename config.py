# config.py
import os
from decimal import Decimal

# --- TELEGRAM ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# --- EXCHANGE ---
EXCHANGE_ID = os.getenv("EXCHANGE_ID", "blofin")

EXCHANGE_EXTRA = {}  # Add {"defaultType":"future"} if Blofin requires it.

EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY", "")
EXCHANGE_API_SECRET = os.getenv("EXCHANGE_API_SECRET", "")
EXCHANGE_API_PASSPHRASE = os.getenv("EXCHANGE_API_PASSPHRASE", "")  # REQUIRED for Blofin!

CREATE_MARKET_BUY_REQUIRES_PRICE = os.getenv("CREATE_MARKET_BUY_REQUIRES_PRICE", "false").lower() == "true"

# TRADING SETTINGS
PAIRS = os.getenv("PAIRS", "BTC/USDT,SUI/USDT").split(",")

QUOTE_ASSET = os.getenv("QUOTE_ASSET", "USDT")

ALLOCATION_PER_PAIR = Decimal(os.getenv("ALLOCATION_PER_PAIR", "0.25"))
MIN_ORDER = Decimal(os.getenv("MIN_ORDER", "5.5"))
LEVERAGE = int(os.getenv("LEVERAGE", "1"))

GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "30"))

LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() == "true"

VERBOSE = os.getenv("VERBOSE", "true").lower() == "true"

