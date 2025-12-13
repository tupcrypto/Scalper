import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

EXCHANGE_ID = "bybit"
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", "").split(",")]

LEVERAGE = int(os.getenv("LEVERAGE", "3"))
GRID_GAP_PCT = float(os.getenv("GRID_GAP_PCT", "0.003"))
ORDER_USDT = float(os.getenv("ORDER_USDT", "6"))
GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "15"))

