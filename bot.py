import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import scanner
import grid_engine
import notifier

# === GLOBAL MEMORY ===
AUTO_TRADING = False
PAIR = config.PAIR

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = True
    await update.message.reply_text(f"🤖 Auto Scalper Started for {PAIR}")
    await notifier.send(f"🤖 Auto Scalper Started for {PAIR}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = False
    grid_engine.close_all_positions()
    await update.message.reply_text("🛑 Auto Scalper Stopped")
    await notifier.send("🛑 Auto Scalper Stopped — All Positions Closed")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = grid_engine.get_status()
    await update.message.reply_text(msg)

async def resetgrid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grid_engine.reset_grid()
    await update.message.reply_text("♻️ Grid Re-centered")
    await notifier.send("♻️ Grid Re-centered")

async def run_loop():
    global AUTO_TRADING
    while True:
        if AUTO_TRADING:
            # scan for a valid micro-range
            grid_range = await scanner.detect_range(PAIR)
            if grid_range:
                await grid_engine.execute(PAIR, grid_range)
        await asyncio.sleep(3)  # small cycle

async def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("resetgrid", resetgrid))

    asyncio.create_task(run_loop())

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
