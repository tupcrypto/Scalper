# bot.py
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import grid_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"BOT STARTED — GRID RUNNING\nPairs: {', '.join([b+'USDT' for b in config.PAIRS_BASE])}")
    # run grid loop as job repeating
    context.application.job_queue.run_repeating(grid_loop_job, interval=config.GRID_LOOP_SECONDS, first=1, name="grid_loop")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # stop repeating job(s)
    jobs = context.application.job_queue.get_jobs_by_name("grid_loop")
    for j in jobs:
        j.schedule_removal()
    await update.message.reply_text("BOT STOPPED — Grid jobs removed")


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = await grid_engine.get_balance()
    msg = f"SCAN DEBUG — BALANCE: {bal:.2f} USDT\n\n"
    # for each base, resolve futures market and price
    for base in config.PAIRS_BASE:
        m = await grid_engine.get_market_symbol_for_base(base)
        if m is None:
            msg += f"{base}USDT: market not found\n"
            continue
        price = await grid_engine.get_price(m)
        msg += f"{m}: price={price}\n"
    await update.message.reply_text(msg)


async def markets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mks = await grid_engine.get_markets_list()
    if not mks:
        await update.message.reply_text("No markets available or failed to load.")
        return
    text = "Markets (first 50):\n\n" + "\n".join(mks[:50])
    await update.message.reply_text(text)


async def grid_loop_job(context: ContextTypes.DEFAULT_TYPE):
    # for each base in config, resolve market and then run grid
    for base in config.PAIRS_BASE:
        symbol = await grid_engine.get_market_symbol_for_base(base)
        if not symbol:
            logger.error(f"[GRID LOOP] market not found for base {base}")
            continue
        price = await grid_engine.get_price(symbol)
        if price is None:
            logger.error(f"[GRID LOOP] price N/A for {symbol}")
            continue
        # run grid logic
        await grid_engine.run_grid_for_symbol(symbol, price)


async def main():
    # build telegram application
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("markets", markets_command))

    # initialize and run
    await app.initialize()
    await app.start()
    # start polling (non-blocking)
    await app.updater.start_polling()

    # keep the program alive until killed
    try:
        await asyncio.Event().wait()
    finally:
        # cleanup: stop updater and close exchange
        await app.updater.stop()
        await app.stop()
        await grid_engine.close_exchange()


if __name__ == "__main__":
    asyncio.run(main())
