# config.py
import os

# ---------------------------------------------------------
# 🔹 TELEGRAM
# ---------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "").strip()

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN missing in Render environment.")

# ---------------------------------------------------------
# 🔹 EXCHANGE (BLOFIN)
# ---------------------------------------------------------
EXCHANGE_ID = os.getenv("EXCHANGE_ID", "blofin").strip()

API_KEY      = os.getenv("BLOFIN_API_KEY", "").strip()
API_SECRET   = os.getenv("BLOFIN_API_SECRET", "").strip()
API_PASSWORD = os.getenv("BLOFIN_PASSWORD", "").strip()  # passphrase

if not API_KEY or not API_SECRET or not API_PASSWORD:
    raise ValueError("❌ Missing one of BLOFIN_API_KEY / BLOFIN_API_SECRET / BLOFIN_PASSWORD in environment!")

# ---------------------------------------------------------
# 🔹 SYMBOLS (your preferred pairs)
# ---------------------------------------------------------
PAIRS = os.getenv("PAIRS", "BTCUSDT,SUIUSDT")
SYMBOLS = [s.strip() for s in PAIRS.split(",") if s.strip()]

# ---------------------------------------------------------
# 🔹 GRID + ORDER SETTINGS
# ---------------------------------------------------------
GRID_INTERVAL = int(os.getenv("GRID_INTERVAL", "15"))   # seconds
EXECUTE_ORDERS = os.getenv("EXECUTE_ORDERS", "true").lower() == "true"
TRADE_USDT_PER_SYMBOL = float(os.getenv("TRADE_USDT_PER_SYMBOL", "10"))

DEBUG = os.getenv("DEBUG", "true").lower() == "true"

