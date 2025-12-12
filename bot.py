# bot.py

import asyncio
import logging
from telegram.ext import Application, CommandHandler
import config
from blofin_api import get_exchange
from grid_engine import GridManager
from scanner import scan_symbols

logging.basicConfig(level=logging.INFO)

GRID_TASKS = []

async def start(update, context):
    await update.message.reply_text("BOT STARTED — GRID RUNNING\nPairs: " + ", ".join(config.SYMBOLS))

    exchange = await get_exchange()
    grid = GridManager(exchange, config.SYMBOLS, context.bot)

    for sym in config.SYMBOLS:
        task = asyncio.create_task(grid.run_grid_loop(sym))
        GRID_TASKS.append(task)

async def scan(update, context):
    exchange = await get_exchange()
    grid = GridManager(exchange, config.SYMBOLS, context.bot)
    result = await scan_symbols(grid)
    await update.message.reply_text(result)

async def markets(update, context):
    exchange = await get_exchange()
    await exchange.load_markets()

    lines = []
    for sym in config.SYMBOLS:
        if sym in exchange.markets:
            lines.append(f"{sym}: FOUND")
        else:
            lines.append(f"{sym}: NOT FOUND")

    await update.message.reply_text("\n".join(lines))

async def list_markets(update, context):
    """Dump Blofin swap market list"""
    exchange = await get_exchange()
    markets = await exchange.load_markets()

    lines = []
    for m in markets:
        try:
            if markets[m]["type"] == "swap":   # futures only
                lines.append(m)
        except:
            pass

    if not lines:
        lines.append("NO SWAP MARKETS FOUND (this means wrong credential or Blofin changed API)")

    msg = "Available Blofin Futures Markets:\n" + "\n".join(lines)
    await update.message.reply_text(msg)

def main():
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("markets", markets))
    app.add_handler(CommandHandler("list", list_markets))

    app.run_polling()

if __name__ == "__main__":
    main()

