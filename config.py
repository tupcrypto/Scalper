import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

BITGET_API_KEY = os.getenv("BITGET_API_KEY")
BITGET_API_SECRET = os.getenv("BITGET_API_SECRET")
BITGET_API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")

LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

MAX_CAPITAL_PCT = float(os.getenv("MAX_CAPITAL_PCT", "100"))

LEVERAGE = int(os.getenv("LEVERAGE", "1"))

raw_pairs = os.getenv("PAIRS", "BTC/USDT,SUI/USDT")
PAIRS = [p.strip() for p in raw_pairs.split(",")]

