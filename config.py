# config.py
import os
from decimal import Decimal

def env_required(key: str, default=None, required=False):
    v = os.environ.get(key, default)
    if required and (v is None or v == ""):
        raise ValueError(f"❌ {key} missing for Blofin in Render Environment.")
    return v

# TELEGRAM
TELEGRAM_BOT_TOKEN = env_required("TELEGRAM_BOT_TOKEN", required=True)

# BLOFIN credentials (password may be required by some exchanges)
BLOFIN_API_KEY = env_required("BLOFIN_API_KEY", required=True)
BLOFIN_API_SECRET = env_required("BLOFIN_API_SECRET", required=True)
BLOFIN_PASSWORD = env_required("BLOFIN_PASSWORD", default="")  # optional; keep empty if not needed

# SYMBOLS list - exact symbols you confirmed
SYMBOLS = [s.strip().upper() for s in env_required("SYMBOLS", default="BTCUSDT,SUIUSDT").split(",")]

# Risk & grid config
GRID_LOOP_SECONDS = int(env_required("GRID_LOOP_SECONDS", default="8"))
MIN_ORDER_USDT = Decimal(env_required("MIN_ORDER_USDT", default="5.5"))  # minimum order cost in USDT (exchange-dependent)
TRADE_USDT_PER_SYMBOL = Decimal(env_required("TRADE_USDT_PER_SYMBOL", default="10"))  # how much USDT to allocate per entry

# Execute orders? (use "true" or "1" to allow live orders)
EXECUTE_ORDERS = env_required("EXECUTE_ORDERS", default="false").lower() in ("1", "true", "yes")

# Logging / debug
DEBUG = env_required("DEBUG", default="false").lower() in ("1", "true", "yes")

