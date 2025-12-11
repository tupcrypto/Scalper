# bot.py
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
import config
import grid_engine
import traceback
import html

RUNNING = False

# ------------------------------------
#   /start
# ------------------------------------
async def start(update, context):
    global RUNNING
    RUNNING = True
    await update.message.reply_text(
        f"BOT STARTED — GRID RUNNING\nPairs: {', '.join(config.PAIRS)}"
    )

    asyncio.create_task(grid_loop(context.bot))


# ------------------------------------
#   /stop
# ------------------------------------
async def stop(update, context):
    global RUNNING
    RUNNING = False
    await update.message.reply_text("BOT STOPPED.")


# ------------------------------------
#   /scan
# ------------------------------------
async def scan(update, context):
    exchange = await grid_engine.get_exchange()
    bal = await grid_engine.get_futures_balance(exchange)

    reply = f"SCAN DEBUG — BALANCE: {bal} USDT\n\n"

    for s in config.PAIRS:
        price = await grid_engine.get_price(exchange, s)
        reply += f"{s}: price={price}\n"

    await update.message.reply_text(reply)

    await exchange.close()


# ------------------------------------
#   GRID LOOP
# ------------------------------------
async def grid_loop(bot):
    global RUNNING

    while RUNNING:
        try:
            exchange = await grid_engine.get_exchange()
            bal = await grid_engine.get_futures_balance(exchange)

            for s in config.PAIRS:
                result = await grid_engine.run_grid(exchange, s, bal)
                await bot.send_message(config.TELEGRAM_CHAT_ID, result)

            await exchange.close()

        except Exception as e:
            err = html.escape(str(e))
            await bot.send_message(config.TELEGRAM_CHAT_ID, f"[GRID LOOP ERROR]\n{err}")

        await asyncio.sleep(config.GRID_LOOP_SECONDS)


# ------------------------------------
#   MAIN
# ------------------------------------
def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("scan", scan))
    app.run_polling()


if __name__ == "__main__":
    main()
