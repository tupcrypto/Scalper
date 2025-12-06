import os

# --- API KEYS FROM ENV ---
BINGX_API_KEY    = os.getenv("BINGX_API_KEY", "")
BINGX_API_SECRET = os.getenv("BINGX_API_SECRET", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID            = os.getenv("TELEGRAM_CHAT_ID", "")  # your personal TG ID

# --- TRADING SETTINGS ---
PAIR            = os.getenv("PAIR", "BTC/USDT")
LEVERAGE        = int(os.getenv("LEVERAGE", "2"))
MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "25"))  # % of account used

# runtime flag (don’t touch)
GRID_ACTIVE = False
