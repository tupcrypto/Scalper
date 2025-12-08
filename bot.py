# ==========================================
# bot.py (FULL FILE – REPLACE EVERYTHING)
# ==========================================

import asyncio
import ccxt
import config
import grid_engine

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)


# ==========================================
# EXCHANGE INIT
# ==========================================

def get_exchange():
    return ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
    })


# ==========================================
# GET BALANCE
# ==========================================

async def get_balance():
    try:
        exchange = get_exchange()
        balance = exchange.fetch_balance()
        futures = balance.get("USDT", {})

        total = futures.get("total", 0)

        return float(total)

    except Exception as e:
        return 0.0


# ==========================================
# SCAN COMMAND
# ==========================================

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = await get_balance()

    msg = f"SCAN DEBUG — BALANCE: {balance:.2f} USDT\n"

    exchange = get_exchange()

    for pair in config.PAIRS:
        try:
            ticker = exchange.fetch_ticker(pair)
            price = ticker["last"]

            action = grid_engine.check_grid_signal(price, balance)

            if isinstance(action, dict):
                msg += f"{pair}: price={price}\n"
                msg += f"{pair}: {action['action']} — {action['reason']}\n\n"
            else:
                msg += f"{pair}: price={price}\n"
                msg += f"{pair}: No grid action\n\n"

        except Exception as e:
            msg += f"{pair}: ERROR - {str(e)}\n"

    await update.message.reply_text(msg)


# ==========================================
# AUTO GRID LOOP
# ==========================================

async def grid_loop(context: ContextTypes.DEFAULT_TYPE):
    exchange = get_exchange()

    balance = await get_balance()

    for pair in config.PAIRS:
        try:
            ticker = exchange.fetch_ticker(pair)
            price = ticker["last"]

            decision = grid_engine.check_grid_signal(price, balance)

            # HOLD → skip
            if decision["action"] == "HOLD":
                continue

            amount = float(decision["amount"])

            if amount <= 0:
                continue

            if decision["action"] == "BUY":
                order = exchange.create_market_buy_order(pair, amount)

            elif decision["action"] == "SELL":
                order = exchange.create_market_sell_order(pair, amount)

            text = f"""
GRID TRADE EXECUTED 🚀
PAIR: {pair}
ACTION: {decision['action']}
AMOUNT: {amount}
REASON: {decision['reason']}
"""
            await context.bot.send_message(config.TELEGRAM_CHAT_ID, text)

        except Exception as e:
            await context.bot.send_message(config.TELEGRAM_CHAT_ID, f"[GRID LOOP ERROR]\n{str(e)}")


# ==========================================
# START COMMAND
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job = context.job_queue.run_repeating(grid_loop, interval=120)
    await update.message.reply_text("AUTO GRID STARTED 👍")


# ==========================================
# MAIN
# ==========================================

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("start", start))

    app.run_polling()


if __name__ == "__main__":
    main()
