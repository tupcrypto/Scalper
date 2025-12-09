# ===============================================
# grid_engine.py  (DEBUG FUTURES BALANCE VERSION)
# ===============================================

import asyncio
import ccxt
import config


# =====================================================
# INIT BITGET EXCHANGE (FUTURES MODE)
# =====================================================
def get_exchange():
    ex = ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",     # ensure USDT-M perpetual futures
        },
    })
    return ex


# =====================================================
# DEBUG FUTURES BALANCE — SEND RAW JSON TO TELEGRAM
# =====================================================
async def get_balance(exchange) -> float:
    try:
        # FETCH FUTURES WALLET STRUCTURE
        bal = await asyncio.to_thread(
            exchange.fetch_balance,
            {"type": "swap"}
        )

        # -------------------------------------------------
        # SEND ENTIRE RAW JSON TO TELEGRAM FOR ANALYSIS
        # -------------------------------------------------
        if config.TELEGRAM_CHAT_ID:
            import json
            debug_str = json.dumps(bal, indent=2)

            from telegram import Bot
            bot = Bot(config.TELEGRAM_BOT_TOKEN)

            # Only send first 3800 chars (Telegram message limit)
            await bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=f"RAW FUTURES BALANCE:\n{debug_str[:3800]}"
            )

        # We temporarily return ZERO until we know correct key
        return 0.0

    except Exception as e:
        print(f"BALANCE ERROR: {e}")
        return 0.0


# =====================================================
# PRICE FETCH
# =====================================================
async def get_price(exchange, pair: str) -> float:
    try:
        ticker = await asyncio.to_thread(exchange.fetch_ticker, pair)
        return float(ticker["last"])
    except Exception:
        return 0.0


# =====================================================
# SIMPLE SIGNAL LOGIC (PLACEHOLDER)
# =====================================================
def check_grid_signal(price, balance, aggressive=True):
    if balance <= 0:
        return "NO BALANCE"

    # Randomized placeholder — will be replaced after balance works
    import random
    r = random.random()

    if r < 0.33:
        return "LONG"
    elif r < 0.66:
        return "SHORT"
    else:
        return "HOLD"


# =====================================================
# EXECUTE ORDER IF LIVE MODE
# =====================================================
async def execute_order(exchange, pair, action, balance):
    if not config.LIVE_TRADING:
        print(f"[SIMULATION] {action} — {pair}")
        return

    try:
        qty = balance * (config.MAX_CAPITAL_PCT / 100)
        if qty <= 0:
            print("NO CAPITAL")
            return

        if action == "LONG":
            await asyncio.to_thread(
                exchange.create_market_buy_order,
                pair,
                qty
            )

        if action == "SHORT":
            await asyncio.to_thread(
                exchange.create_market_sell_order,
                pair,
                qty
            )

        print(f"[LIVE TRADE] {action} — {pair} — qty={qty}")

    except Exception as e:
        print(f"[ORDER ERROR] {e}")
