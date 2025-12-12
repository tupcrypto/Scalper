import asyncio
import logging
from telegram.ext import Application, CommandHandler

import config
from blofin_api import get_exchange
from grid_engine import GridManager
from scanner import scan_symbols

logging.basicConfig(level=logging.INFO)

GRID_TASKS_STARTED = False
GRID_MANAGER = None

async def start(update, context):
    global GRID_TASKS_STARTED, GRID_MANAGER

    await update.message.reply_text(
        "BOT STARTED — GRID RUNNING\nPairs: " + ", ".join(config.SYMBOLS)
    )

    if GRID_TASKS_STARTED:
        return

    exchange = await get_exchange()
    GRID_MANAGER = GridManager(exchange, config.SYMBOLS, context.bot)

    # start grid loops NON-BLOCKING
    for sym in config.SYMBOLS:
        asyncio.create_task(GRID_MANAGER.run_grid_loop(sym))

    GRID_TASKS_STARTED = True


async def scan(update, context):
    result = await scan_symbols(GRID_MANAGER)
    await update.message.reply_text(result)


async def markets(update, context):
    exchange = await get_exchange()
    await exchange.load_markets()

    txt = ""
    for sym in config.SYMBOLS:
        txt += f"{sym}: {'FOUND' if sym in exchange.markets else 'NOT FOUND'}\n"

    await update.message.reply_text(txt)


async def list_markets(update, context):
    exchange = await get_exchange()
    markets = exchange.markets

    txt = "Blofin Futures Markets:\n"
    for m in markets:
        try:
            if markets[m]["type"] == "swap":
                txt += m + "\n"
        except:
            pass

    await update.message.reply_text(txt[:4000])


def main():
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("markets", markets))
    app.add_handler(CommandHandler("list", list_markets))

    app.run_polling()


if __name__ == "__main__":
    main()
