# bot.py
import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

import config
from grid_engine import GridManager
from blofin_api import BlofinAsync
import asyncio

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("scalper")

GRID = None
EXCHANGE = None
TASKS = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GRID, EXCHANGE, TASKS
    chat = update.effective_chat

    await update.message.reply_text("BOT STARTED — GRID RUNNING")

    if EXCHANGE is None:
        EXCHANGE = BlofinAsync(
            config.BLOFIN_API_KEY,
            config.BLOFIN_API_SECRET,
            config.BLOFIN_PASSWORD,
        )

    if GRID is None:
        GRID = GridManager(EXCHANGE, config.SYMBOLS, context.bot)

    # start loops
    for sym in config.SYMBOLS:
        if sym not in TASKS:
            TASKS[sym] = asyncio.create_task(GRID.run_grid_loop(sym))

    await update.message.reply_text(f"Pairs: {', '.join(config.SYMBOLS)}")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TASKS, EXCHANGE, GRID

    await update.message.reply_text("Stopping grid tasks...")

    for sym, task in list(TASKS.items()):
        task.cancel()
        TASKS.pop(sym, None)

    if EXCHANGE:
        await EXCHANGE.close()
        EXCHANGE = None

    GRID = None
    await update.message.reply_text("All grid tasks stopped.")


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GRID, EXCHANGE

    await update.message.reply_text("Running scan...")

    if EXCHANGE is None:
        EXCHANGE = BlofinAsync(
            config.BLOFIN_API_KEY,
            config.BLOFIN_API_SECRET,
            config.BLOFIN_PASSWORD,
        )

    if GRID is None:
        GRID = GridManager(EXCHANGE, config.SYMBOLS, context.bot)

    r = await GRID.scan_all()
    msg = f"SCAN DEBUG — BALANCE: {r['balance']:.2f} USDT\n\n" + "\n".join(r["lines"])
    await update.message.reply_text(msg)


async def markets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global EXCHANGE

    if EXCHANGE is None:
        EXCHANGE = BlofinAsync(
            config.BLOFIN_API_KEY,
            config.BLOFIN_API_SECRET,
            config.BLOFIN_PASSWORD,
        )

    try:
        data = await EXCHANGE.fetch_markets_info(config.SYMBOLS)
        text = "\n".join(data)
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


def main():
    """IMPORTANT: non-async main due to Render background worker limitations"""
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("markets", markets_command))

    logger.info("Bot polling started (Render-safe)...")

    # IMPORTANT FIX: no event loop closing issues
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()

