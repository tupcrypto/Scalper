# config.py
import os
from typing import List

# Exchange selection: 'blofin'
EXCHANGE_ID = os.getenv("EXCHANGE_ID", "blofin")

# API credentials for the exchange
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY", "")
EXCHANGE_API_SECRET = os.getenv("EXCHANGE_API_SECRET", "")
EXCHANGE_API_PASSWORD = os.getenv("EXCHANGE_API_PASSWORD", "")  # some exchanges require

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Trading pairs (comma-separated env var)
PAIRS: List[str] = [p.strip().upper() for p in os.getenv("PAIRS", "BTC/USDT,SUI/USDT").split(",") if p.strip()]

# Per-pair settings
LEVERAGE = int(os.getenv("LEVERAGE", "3"))  # max allowed leverage (if used on exchange)
MIN_ORDER_USDT = float(os.getenv("MIN_ORDER_USDT", "6.0"))  # minimum USD (quote) to spend per order
MAX_BALANCE_USAGE_PCT = float(os.getenv("MAX_BALANCE_USAGE_PCT", "0.5"))  # fraction of total USDT for trading (0-1)

# Trading / grid loop settings
GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "30"))
SCAN_ONLY = os.getenv("SCAN_ONLY", "false").lower() in ("1", "true", "yes")

# Price slippage / order offsets (for limit orders)
PRICE_OFFSET_BUY_PCT = float(os.getenv("PRICE_OFFSET_BUY_PCT", "0.001"))   # 0.1% above market for buy (limit)
PRICE_OFFSET_SELL_PCT = float(os.getenv("PRICE_OFFSET_SELL_PCT", "0.001")) # 0.1% below market for sell (limit)

# Logging / debug
DEBUG = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")
