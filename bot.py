from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import grid_engine
from config import *

RUNNING = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUNNING
    RUNNING = True
    await update.message.reply_text(
        f"✅ GRID STARTED (Bybit Futures)\nPairs: {', '.join(SYMBOLS)}"
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUNNING
    RUNNING = False
    await update.message.reply_text("🛑 GRID STOPPED")

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = await grid_engine.get_balance()
    msg = f"Balance: {bal:.2f} USDT\n\n"
    for s in SYMBOLS:
        try:
            p = await grid_engine.get_price(s)
            msg += f"{s}: {p}\n"
        except Exception as e:
            msg += f"{s}: ERROR\n"
    await update.message.reply_text(msg)

async def grid_loop(app):
    global RUNNING
    while True:
        if RUNNING:
            for s in SYMBOLS:
                try:
                    await grid_engine.grid_step(s)
                except Exception as e:
                    print(f"{s} GRID ERROR:", e)
        await asyncio.sleep(GRID_LOOP_SECONDS)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("scan", scan))

    app.post_init = lambda _: asyncio.create_task(grid_loop(app))

    app.run_polling()

if __name__ == "__main__":
    main()

