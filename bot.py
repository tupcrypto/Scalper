# ===========================
# bot.py  (GRID BOT)
# ===========================
import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler

import config
import grid_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

GRID_TASK = None


# -------------------------------------------------------
# /scan COMMAND
# -------------------------------------------------------
async def scan(update, context):
    try:
        exchange = grid_engine.get_exchange()
        balance = grid_engine.get_assumed_balance()

        resp = f"SCAN DEBUG — BALANCE: {balance:.2f} USDT\n\n"

        for pair in config.PAIRS:
            price = await grid_engine.get_price(exchange, pair)
            if price == 0:
                resp += f"{pair}: ❌ price unavailable\n"
                continue

            signal = grid_engine.check_grid_signal(pair, price, balance)

            resp += f"{pair}: price={price}\n"
            resp += f"{pair}: {signal}\n\n"

        await update.message.reply_text(resp)

    except Exception as e:
        await update.message.reply_text(f"SCAN ERROR:\n{str(e)}")


# -------------------------------------------------------
# GRID AUTO-LOOP
# -------------------------------------------------------
async def grid_loop(app):
    exchange = grid_engine.get_exchange()

    while True:
        try:
            balance = grid_engine.get_assumed_balance()

            for pair in config.PAIRS:
                price = await grid_engine.get_price(exchange, pair)
                signal = grid_engine.check_grid_signal(pair, price, balance)

                # broadcast grid signal
                if config.TELEGRAM_CHAT_ID:
                    await app.bot.send_message(
                        chat_id=config.TELEGRAM_CHAT_ID,
                        text=f"[GRID] {pair} — {signal}"
                    )

                # execute real trades if LIVE
                result = await grid_engine.execute_order(
                    exchange, pair, signal, balance
                )

                if (
                    config.LIVE_TRADING
                    and config.TELEGRAM_CHAT_ID
                    and "ORDER" in result
                ):
                    await app.bot.send_message(
                        chat_id=config.TELEGRAM_CHAT_ID,
                        text=result
                    )

        except Exception as e:
            if config.TELEGRAM_CHAT_ID:
                await app.bot.send_message(
                    chat_id=config.TELEGRAM_CHAT_ID,
                    text=f"[GRID LOOP ERROR]\n{str(e)}"
                )

        await asyncio.sleep(30)


# -------------------------------------------------------
# /start COMMAND
# -------------------------------------------------------
async def start(update, context):
    global GRID_TASK

    await update.message.reply_text("BOT STARTED — PIONEX-STYLE NEUTRAL GRID")

    if GRID_TASK:
        GRID_TASK.cancel()

    app = context.application
    GRID_TASK = asyncio.create_task(grid_loop(app))


# -------------------------------------------------------
# /stop COMMAND
# -------------------------------------------------------
async def stop(update, context):
    global GRID_TASK

    if GRID_TASK:
        GRID_TASK.cancel()
        GRID_TASK = None

    await update.message.reply_text("AUTO GRID LOOP STOPPED")


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    logging.info("BOT RUNNING — POLLING MODE")
    app.run_polling()


if __name__ == "__main__":
    main()
