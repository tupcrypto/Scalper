# config.py
# Full file - keep secrets out of git; on Render set as environment variables.

import os
from decimal import Decimal

# --- TELEGRAM ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")  # required

# --- EXCHANGE / CCXT ---
# Use lowercase exchange id as used by ccxt (e.g. "blofin", "bitget", "binance", etc.)
EXCHANGE_ID = os.getenv("EXCHANGE_ID", "blofin")

# For some exchanges you may need extra params. Example for futures (uncomment if needed):
# EXCHANGE_EXTRA = {"defaultType": "future"}  # or {"defaultType":"swap"} etc.
EXCHANGE_EXTRA = {}

# API credentials - set as env vars on Render:
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY", "")
EXCHANGE_API_SECRET = os.getenv("EXCHANGE_API_SECRET", "")
# some exchanges require a passphrase / password
EXCHANGE_API_PASSPHRASE = os.getenv("EXCHANGE_API_PASSPHRASE", "")

# Optionally force ccxt market buy behavior if required by the exchange
# (set to True if the exchange requires price for market buy orders)
CREATE_MARKET_BUY_REQUIRES_PRICE = os.getenv("CREATE_MARKET_BUY_REQUIRES_PRICE", "false").lower() == "true"

# --- TRADING PAIRS & SIZING ---
# Comma-separated list or override in code
PAIRS = os.getenv("PAIRS", "BTC/USDT,SUI/USDT").split(",")

# Which wallet to read for balance (often 'USDT' for futures)
QUOTE_ASSET = os.getenv("QUOTE_ASSET", "USDT")

# Allocation per pair (fraction of total balance to use for each entry)
ALLOCATION_PER_PAIR = Decimal(os.getenv("ALLOCATION_PER_PAIR", "0.25"))  # 25% per pair as default

# Min order (in quote currency). If unknown, set a safe tiny value (exchange will reject if too small).
MIN_ORDER = Decimal(os.getenv("MIN_ORDER", "5.5"))

# Leverage (if using futures). Leave 1 for spot
LEVERAGE = int(os.getenv("LEVERAGE", "1"))

# Grid loop interval in seconds
GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "30"))

# Safety: enabled trading or only simulate
LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() == "true"

# Log verbosity
VERBOSE = os.getenv("VERBOSE", "true").lower() == "true"
