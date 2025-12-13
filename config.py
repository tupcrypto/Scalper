import os

# ===== Telegram =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# ===== Exchange =====
EXCHANGE_ID = "bitunix"

API_KEY = os.getenv("BITUNIX_API_KEY")
API_SECRET = os.getenv("BITUNIX_API_SECRET")

# ===== Trading =====
PAIRS = [p.strip() for p in os.getenv(
    "PAIRS", "BTC/USDT:USDT,SUI/USDT:USDT"
).split(",")]

LEVERAGE = int(os.getenv("LEVERAGE", "3"))
GRID_LEVELS = int(os.getenv("GRID_LEVELS", "20"))
GRID_RANGE_PERCENT = float(os.getenv("GRID_RANGE_PERCENT", "5"))
USDT_PER_GRID = float(os.getenv("USDT_PER_GRID", "5"))

GRID_LOOP_SECONDS = int(os.getenv("GRID_LOOP_SECONDS", "10"))
EXECUTE_ORDERS = os.getenv("EXECUTE_ORDERS", "true").lower() == "true"

DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# ===== Validation =====
missing = []
for k, v in {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
}.items():
    if not v:
        missing.append(k)

if missing:
    raise RuntimeError(f"Missing env vars: {', '.join(missing)}")
