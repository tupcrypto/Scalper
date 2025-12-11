import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import grid_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ------------------------------------------------
# /start
# ------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("BOT STARTED — GRID RUNNING")
    context.application.job_queue.run_repeating(grid_loop, interval=config.GRID_INTERVAL, first=1)


# ------------------------------------------------
# /scan
# ------------------------------------------------
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = await grid_engine.get_balance()
    msg = f"SCAN — Balance: {bal:.2f} USDT\n\n"

    for s in config.PAIRS:
        price = await grid_engine.get_price(s)
        msg += f"{s}: Price = {price}\n"

    await update.message.reply_text(msg)


# ------------------------------------------------
# /markets  (NEW)
# ------------------------------------------------
async def markets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mks = await grid_engine.get_markets()
    if not mks:
        await update.message.reply_text("No markets loaded.")
        return

    text = "Available Markets (first 50):\n\n"
    text += "\n".join(mks[:50])

    await update.message.reply_text(text)


# ------------------------------------------------
# /stop
# ------------------------------------------------
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.application.job_queue.stop()
    await update.message.reply_text("🛑 GRID STOPPED")


# ------------------------------------------------
# GRID LOOP
# ------------------------------------------------
async def grid_loop(context: ContextTypes.DEFAULT_TYPE):
    try:
        for s in config.PAIRS:
            price = await grid_engine.get_price(s)
            if price is None:
                logger.error(f"[GRID] {s} PRICE N/A")
                continue

            await grid_engine.run_grid(s, price)

    except Exception as e:
        logger.error(f"[GRID LOOP ERROR] {e}")


# ------------------------------------------------
# MAIN LOOP (BACKGROUND WORKER SAFE)
# ------------------------------------------------
async def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("markets", markets))
    app.add_handler(CommandHandler("stop", stop))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await asyncio.Event().wait()   # Keep alive


if __name__ == "__main__":
    asyncio.run(main())
