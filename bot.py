import asyncio
import logging
import ccxt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import grid_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# TELEGRAM COMMANDS
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("BOT STARTED — GRID RUNNING")
    context.application.job_queue.run_repeating(grid_loop, interval=config.GRID_INTERVAL, first=1)
    

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = await grid_engine.get_balance()
    prices = {}

    for sym in config.PAIRS:
        try:
            prices[sym] = await grid_engine.get_price(sym)
        except:
            prices[sym] = "N/A"

    msg = f"SCAN DEBUG — BALANCE: {balance:.2f} USDT\n\n"

    for s in config.PAIRS:
        msg += f"{s}: price={prices[s]}\n"

    await update.message.reply_text(msg)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.application.job_queue.stop()
    await update.message.reply_text("🛑 GRID STOPPED")


# -----------------------------
# GRID LOOP
# -----------------------------
async def grid_loop(context: ContextTypes.DEFAULT_TYPE):
    try:
        for sym in config.PAIRS:
            price = await grid_engine.get_price(sym)
            if price is None:
                logger.error(f"[GRID] {sym} — price N/A")
                continue

            await grid_engine.run_grid(sym, price)

    except Exception as e:
        logger.error(f"[GRID LOOP ERROR] {e}")


# -----------------------------
# MAIN ENTRYPOINT (Worker Safe)
# -----------------------------
async def main():
    application = (
        ApplicationBuilder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("scan", scan))
    application.add_handler(CommandHandler("stop", stop))

    # Start polling inside background worker
    logger.info("📡 Telegram bot polling started…")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # KEEP WORKER ALIVE FOREVER
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually")
