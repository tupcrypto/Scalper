# config.py
# Replace values below with your real values BEFORE starting the bot.

TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Exchange credentials (Blofin in your case)
API_KEY = "YOUR_BLOFIN_API_KEY"
API_SECRET = "YOUR_BLOFIN_API_SECRET"
API_PASSWORD = "YOUR_BLOFIN_API_PASSWORD"   # often required by futures exchanges

# Which exchange id to use (ccxt id)
EXCHANGE_ID = "blofin"

# Treat symbols as futures (this file is for FUTURES)
FUTURES = True

# Grid / trading config:
GRID_LOOP_SECONDS = 5         # how often grid loop runs
ORDER_SIZE_USDT = 10.0        # per order size in USDT (adjust to minimums)
MAX_PAIRS = 6                 # how many pairs to run simultaneously

# Pairs you want the bot to attempt (base only or common variants)
# We'll autodetect correct futures market for each base
PAIRS_BASE = ["BTC", "SUI"]   # base assets; bot will search for a futures market with USDT quote
