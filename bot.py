# ======================================================
# bot.py — FINAL CLEAN SCALPER BOT
# ======================================================

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
import grid_engine

RUN_FLAG = False


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUN_FLAG
    RUN_FLAG = True
    await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text="BOT STARTED — GRID MODE ACTIVE")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUN_FLAG
    RUN_FLAG = False
    await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text="BOT STOPPED")


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        exchange = grid_engine.get_exchange()
        if exchange is None:
            await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text="SCAN ERROR — EXCHANGE INIT FAILED")
            return

        bal = grid_engine.get_balance()
        out = "SCAN DEBUG — BALANCE: " + str(bal) + " USDT\n\n"

        for sym in config.PAIRS:
            px = grid_engine.get_price(exchange, sym)
            out = out + sym + ": price=" + str(px) + "\n"

            sig = grid_engine.check_grid_signal(sym, px, bal)
            out = out + sym + ": " + sig + "\n\n"

        await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=out)
    except Exception as e:
        await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text="SCAN ERROR: " + str(e))


async def grid_loop(app):
    global RUN_FLAG
    exchange = grid_engine.get_exchange()

    while True:
        if RUN_FLAG:
            bal = grid_engine.get_balance()
            for sym in config.PAIRS:
                try:
                    px = grid_engine.get_price(exchange, sym)
                    sig = grid_engine.check_grid_signal(sym, px, bal)

                    msg = "[GRID] " + sym + " — " + sig
                    await app.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=msg)

                    out = grid_engine.execute_order(exchange, sym, sig, bal)
                    await app.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=out)

                except Exception as ex:
                    await app.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text="GRID LOOP ERROR: " + str(ex))

        await asyncio.sleep(120)  # 2 min


async def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("scan", cmd_scan))

    asyncio.create_task(grid_loop(app))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
