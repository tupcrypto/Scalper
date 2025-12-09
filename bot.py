# ======================================================
# bot.py — CLEAN STABLE GRID BOT (BITGET)
# ======================================================

import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler

import config
import grid_engine


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

GRID_TASK = None  # Background loop reference


# ======================================================
# /scan COMMAND  — FIXED, NEVER AWAITS SYNC FUNCTIONS
# ======================================================
async def scan(update, context):
    try:
        ex = grid_engine.get_exchange()
        balance = grid_engine.get_balance()  # sync, returns float

        # no coroutine formatting, no .2f formatting
        resp = f"SCAN DEBUG — BALANCE: {balance} USDT\n\n"

        for pair in config.PAIRS:
            price = grid_engine.get_price(ex, pair)  # sync float

            if price == 0:
                resp += f"{pair}: ❌ price unavailable\n\n"
                continue

            signal = grid_engine.check_grid_signal(pair, price, balance)

            resp += f"{pair}: price={price}\n"
            resp += f"{pair}: {signal}\n\n"

        await update.message.reply_text(resp)

    except Exception as e:
        await update.message.reply_text(f"SCAN ERROR:\n{e}")


# ======================================================
# GRID LOOP — NO AWAIT ON GRID ENGINE FUNCTIONS
# ======================================================
async def grid_loop(app):
    while True:
        try:
            ex = grid_engine.get_exchange()
            balance = grid_engine.get_balance()

            for pair in config.PAIRS:
                price = grid_engine.get_price(ex, pair)
                signal = grid_engine.check_grid_signal(pair, price, balance)

                msg = f"[GRID] {pair} — {signal}"

                # send grid signal to Telegram
                if config.TELEGRAM_CHAT_ID:
                    await app.bot.send_message(
                        chat_id=config.TELEGRAM_CHAT_ID,
                        text=msg
                    )

                # try actual order (sync)
                result = grid_engine.execute_order(ex, pair, signal, balance)

                # only notify when actual order executed or simulated
                if (
                    "ORDER" in result
                    and config.TELEGRAM_CHAT_ID
                ):
                    await app.bot.send_message(
                        chat_id=config.TELEGRAM_CHAT_ID,
                        text=result
                    )

        except Exception as e:
            if config.TELEGRAM_CHAT_ID:
                await app.bot.send_message(
                    chat_id=config.TELEGRAM_CHAT_ID,
                    text=f"[GRID LOOP ERROR]\n{e}"
                )

        await asyncio.sleep(30)  # run cycle every 30 seconds


# ======================================================
# /start COMMAND
# ======================================================
async def start(update, context):
    global GRID_TASK

    await update.message.reply_text("BOT STARTED — PIONEX-STYLE NEUTRAL GRID")

    # cancel existing loop
    if GRID_TASK:
        GRID_TASK.cancel()

    app = context.application
    GRID_TASK = asyncio.create_task(grid_loop(app))


# ======================================================
# /stop COMMAND
# ======================================================
async def stop(update, context):
    global GRID_TASK

    if GRID_TASK:
        GRID_TASK.cancel()
        GRID_TASK = None

    await update.message.reply_text("AUTO GRID LOOP STOPPED")


# ======================================================
# MAIN ENTRY
# ======================================================
def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    logging.info("BOT RUNNING — POLLING MODE (BACKGROUND WORKER)")
    app.run_polling()


if __name__ == "__main__":
    main()
