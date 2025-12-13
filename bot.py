import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import config
from exchange import get_exchange
from grid_engine import NeutralGrid
import threading

exchange = get_exchange()
grid = NeutralGrid(exchange)
grid_thread = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global grid_thread
    if grid_thread and grid_thread.is_alive():
        await update.message.reply_text("Grid already running")
        return

    grid_thread = threading.Thread(target=grid.run, daemon=True)
    grid_thread.start()

    await update.message.reply_text(
        "✅ GRID STARTED\nPairs:\n" + "\n".join(config.PAIRS)
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grid.stop()
    await update.message.reply_text("⛔ GRID STOPPED")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = exchange.fetch_balance()
    usdt = bal["USDT"]["free"]
    await update.message.reply_text(f"💰 Balance: {usdt:.2f} USDT")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = []
    for s in config.PAIRS:
        p = exchange.fetch_ticker(s)["last"]
        msg.append(f"{s}: {p}")
    await update.message.reply_text("\n".join(msg))

async def main():
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("price", price))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
