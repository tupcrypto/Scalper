# ===========================
# bot.py  (FINAL)
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
        balance = await grid_engine.get_balance(exchange)

        resp = f"SCAN DEBUG — BALANCE: {balance:.2f} USDT\n\n"

        for pair in config.PAIRS:
            price = await grid_engine.get_price(exchange, pair)
            if price == 0:
                resp += f"{pair}: ❌ price unavailable\n"
                continue

            action = grid_engine.check_grid_signal(
                price,
                balance,
                aggressive=config.AGGRESSIVE
            )

            resp += f"{pair}: price={price}\n"
            resp += f"{pair}: {action}\n\n"

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
            balance = await grid_engine.get_balance(exchange)

            for pair in config.PAIRS:
                price = await grid_engine.get_price(exchange, pair)
                action = grid_engine.check_grid_signal(price, balance, aggressive=True)

                # log to owner
                if config.TELEGRAM_CHAT_ID:
                    await app.bot.send_message(
                        chat_id=config.TELEGRAM_CHAT_ID,
                        text=f"[GRID] {pair} — {action}"
                    )

                # execute if live mode & actionable
                if config.LIVE_TRADING and ("BUY" in action or "SELL" in action):
                    result = await grid_engine.execute_order(
                        exchange, pair, action, balance
                    )
                    if config.TELEGRAM_CHAT_ID:
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

        await asyncio.sleep(30)  # 30 seconds between scans


# -------------------------------------------------------
# /start COMMAND
# -------------------------------------------------------
async def start(update, context):
    global GRID_TASK

    await update.message.reply_text("BOT STARTED — AGGRESSIVE MODE")

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

    await update.message.reply_text("AUTO LOOP STOPPED")


# -------------------------------------------------------
# MAIN ENTRY (NO asyncio.run!)
# -------------------------------------------------------
def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    logging.info("BOT RUNNING — POLLING MODE (BACKGROUND WORKER)")
    app.run_polling()


if __name__ == "__main__":
    main()
