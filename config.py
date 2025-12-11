import os

# ============================
# TELEGRAM BOT TOKEN
# ============================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN missing! Add it in Render → Environment.")

# ============================
# EXCHANGE SETTINGS
# ============================

EXCHANGE_ID = os.getenv("EXCHANGE_ID", "blofin")  # default blofin

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSWORD = os.getenv("API_PASSWORD")  # required for blofin

if not API_KEY or not API_SECRET:
    raise ValueError("❌ API_KEY or API_SECRET missing in Render Environment.")

if EXCHANGE_ID.lower() == "blofin" and not API_PASSWORD:
    raise ValueError("❌ API_PASSWORD missing for Blofin in Render Environment.")


# ============================
# GRID SETTINGS
# ============================

GRID_PAIRS = os.getenv("GRID_PAIRS", "BTCUSDT,SUIUSDT").split(",")

GRID_INTERVAL_SECONDS = int(os.getenv("GRID_INTERVAL_SECONDS", 5))  # grid loop delay

MIN_ORDER_USDT = float(os.getenv("MIN_ORDER_USDT", 5))  # minimum allowed order


# ============================
# SCANNER SETTINGS
# ============================

SCAN_MIN_BALANCE = float(os.getenv("SCAN_MIN_BALANCE", 1))
SCAN_MIN_VOLUME = float(os.getenv("SCAN_MIN_VOLUME", 10_000_000))  # default 10M volume


# ============================
# DEBUG
# ============================

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
