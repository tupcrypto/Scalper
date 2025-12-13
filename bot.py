# bot.py
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
from exchanges import create_exchange
from grid_engine import GridManager
from scanner import run_scan

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scalper")

EXCHANGE = None
GRID = None

async def ensure_exchange():
    global EXCHANGE, GRID
    if EXCHANGE is None:
        exchange, err = await create_exchange()
        if err:
            return None, err
        EXCHANGE = exchange
        GRID = GridManager(EXCHANGE, config.SYMBOLS)
    return EXCHANGE, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exchange, err = await ensure_exchange()
    if err:
        await update.message.reply_text("❌ " + err)
        return

    await update.message.reply_text("BOT STARTED — GRID RUNNING\nPairs: " + ", ".join(config.SYMBOLS))

    # start grid loops for each symbol (non-blocking)
    for sym in config.SYMBOLS:
        started = await GRID.start_grid_for(sym, loop_seconds=config.GRID_LOOP_SECONDS, notify=lambda msg: context.bot.send_message(chat_id=update.effective_chat.id, text=msg) if False else None)
        logger.info("start grid for %s -> %s", sym, started)

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if GRID is None:
        ex, err = await ensure_exchange()
        if err:
            await update.message.reply_text("❌ " + err)
            return
    out = await run_scan(GRID)
    await update.message.reply_text(out)

async def list_markets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exchange, err = await ensure_exchange()
    if err:
        await update.message.reply_text("❌ " + err)
        return

    # build a list of markets (limit to 2000 chars)
    try:
        markets = sorted(exchange.markets.keys())
        chunks = []
        cur = ""
        for m in markets:
            line = m + "\n"
            if len(cur) + len(line) > 1900:
                chunks.append(cur)
                cur = ""
            cur += line
        if cur:
            chunks.append(cur)
        for chunk in chunks:
            await update.message.reply_text(chunk)
    except Exception as e:
        await update.message.reply_text("Error fetching markets: " + repr(e))

async def markets_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exchange, err = await ensure_exchange()
    if err:
        await update.message.reply_text("❌ " + err)
        return
    txt = ""
    for s in config.SYMBOLS:
        txt += f"{s}: {'FOUND' if s in exchange.markets else 'NOT FOUND'}\n"
    await update.message.reply_text(txt)

def main():
    if not config.TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN missing in env")
        return

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("list", list_markets))
    app.add_handler(CommandHandler("markets", markets_check))

    # run polling (single instance only)
    app.run_polling()

if __name__ == "__main__":
    main()
