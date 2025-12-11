# bot.py
import asyncio
import logging
import os
from decimal import Decimal, ROUND_DOWN
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import config
from grid_engine import GridManager
from blofin_api import BlofinAsync

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("scalper")

APP = None
GRID: GridManager | None = None
EXCHANGE: BlofinAsync | None = None
TASKS = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GRID, EXCHANGE, TASKS
    chat = update.effective_chat
    await context.bot.send_message(chat.id, "BOT STARTED — GRID RUNNING")
    logger.info("Received /start")

    # initialize exchange & grid if not ready
    if EXCHANGE is None:
        await context.bot.send_message(chat.id, "Initializing exchange...")
        EXCHANGE = BlofinAsync(config.BLOFIN_API_KEY, config.BLOFIN_API_SECRET, config.BLOFIN_PASSWORD)

    if GRID is None:
        GRID = GridManager(EXCHANGE, config.SYMBOLS, context.bot)

    # start grid tasks for each symbol if not already running
    for sym in config.SYMBOLS:
        if sym not in TASKS:
            TASKS[sym] = asyncio.create_task(GRID.run_grid_loop(sym))
            logger.info("Started grid loop for %s", sym)

    await context.bot.send_message(chat.id, f"Pairs: {', '.join(config.SYMBOLS)}")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TASKS, GRID, EXCHANGE
    chat = update.effective_chat
    await context.bot.send_message(chat.id, "Stopping grid — cancelling tasks...")
    logger.info("Received /stop")

    for sym, t in list(TASKS.items()):
        t.cancel()
        logger.info("Cancelled task for %s", sym)
        TASKS.pop(sym, None)

    # close exchange connections
    if EXCHANGE:
        await EXCHANGE.close()
        EXCHANGE = None
    GRID = None
    await context.bot.send_message(chat.id, "All grid tasks stopped.")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global EXCHANGE, GRID
    chat = update.effective_chat
    await context.bot.send_message(chat.id, "Running one-shot scan...")
    logger.info("Received /scan")

    if EXCHANGE is None:
        EXCHANGE = BlofinAsync(config.BLOFIN_API_KEY, config.BLOFIN_API_SECRET, config.BLOFIN_PASSWORD)

    if GRID is None:
        GRID = GridManager(EXCHANGE, config.SYMBOLS, context.bot)

    report = await GRID.scan_all()
    await context.bot.send_message(chat.id, f"SCAN DEBUG — BALANCE: {report['balance']:.2f} USDT\n\n" + "\n".join(report["lines"]))

async def markets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global EXCHANGE
    chat = update.effective_chat
    await context.bot.send_message(chat.id, "Fetching markets...")
    logger.info("Received /markets")

    if EXCHANGE is None:
        EXCHANGE = BlofinAsync(config.BLOFIN_API_KEY, config.BLOFIN_API_SECRET, config.BLOFIN_PASSWORD)

    try:
        markets = await EXCHANGE.fetch_markets_info(config.SYMBOLS)
        text = "Markets:\n" + "\n".join(markets)
    except Exception as e:
        logger.exception("markets fetch error")
        text = f"Error fetching markets: {e}"
    await context.bot.send_message(chat.id, text)

async def main():
    global APP
    token = config.TELEGRAM_BOT_TOKEN
    APP = ApplicationBuilder().token(token).build()

    APP.add_handler(CommandHandler("start", start_command))
    APP.add_handler(CommandHandler("stop", stop_command))
    APP.add_handler(CommandHandler("scan", scan_command))
    APP.add_handler(CommandHandler("markets", markets_command))

    logger.info("Starting polling...")
    # run polling (this blocks until cancelled)
    await APP.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down (keyboard interrupt)")
    except Exception:
        logger.exception("Unhandled exception in main")

