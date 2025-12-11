# bot.py
import asyncio
import html
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
)
import config
import grid_engine


RUNNING = False
APP = None


# ------------------------------------------------------
# /markets  — lists all available Blofin markets
# ------------------------------------------------------
async def markets(update, context):
    try:
        exchange = await grid_engine.get_exchange()
        markets = list(exchange.markets.keys())
        await update.message.reply_text(
            "Blofin Markets:\n\n" + "\n".join(markets[:200])
        )
        await exchange.close()
    except Exception as e:
        await update.message.reply_text(f"MARKETS ERROR:\n{html.escape(str(e))}")


# ------------------------------------------------------
# /scan — quick check
# ------------------------------------------------------
async def scan(update, context):
    try:
        exchange = await grid_engine.get_exchange()
        bal = await grid_engine.get_futures_balance(exchange)
        msg = f"SCAN DEBUG BALANCE: {bal}\n\n"

        for sym in config.PAIRS:
            price = await grid_engine.get_price(exchange, sym)
            msg += f"{sym}: {price}\n"

        await update.message.reply_text(msg)
        await exchange.close()

    except Exception as e:
        await update.message.reply_text(f"SCAN ERROR:\n{html.escape(str(e))}")


# ------------------------------------------------------
# /start — begin grid
# ------------------------------------------------------
async def start(update, context):
    global RUNNING
    RUNNING = True

    await update.message.reply_text(
        f"BOT STARTED — GRID RUNNING\nPairs: {config.PAIRS}"
    )

    asyncio.create_task(grid_loop(context.bot))


# ------------------------------------------------------
# /stop — stop grid
# ------------------------------------------------------
async def stop(update, context):
    global RUNNING
    RUNNING = False
    await update.message.reply_text("BOT STOPPED.")


# ------------------------------------------------------
# GRID LOOP
# ------------------------------------------------------
async def grid_loop(bot):
    global RUNNING
    await bot.send_message(config.TELEGRAM_CHAT_ID, "GRID LOOP ACTIVE")

    while RUNNING:
        try:
            exchange = await grid_engine.get_exchange()
            bal = await grid_engine.get_futures_balance(exchange)

            for sym in config.PAIRS:
                try:
                    result = await grid_engine.run_grid(exchange, sym, bal)
                    await bot.send_message(config.TELEGRAM_CHAT_ID, result)
                except Exception as e:
                    await bot.send_message(
                        config.TELEGRAM_CHAT_ID,
                        f"[GRID ERROR] {sym}\n{html.escape(str(e))}",
                    )

            await exchange.close()

        except Exception as e:
            await bot.send_message(
                config.TELEGRAM_CHAT_ID,
                f"[GRID LOOP ERROR]\n{html.escape(str(e))}",
            )

        await asyncio.sleep(config.GRID_LOOP_SECONDS)


# ------------------------------------------------------
# MAIN — starts bot safely
# ------------------------------------------------------
async def main():
    global APP

    APP = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    APP.add_handler(CommandHandler("start", start))
    APP.add_handler(CommandHandler("stop", stop))
    APP.add_handler(CommandHandler("scan", scan))
    APP.add_handler(CommandHandler("markets", markets))

    print(">>> BOT STARTED SUCCESSFULLY — POLLING…")

    await APP.initialize()
    await APP.start()
    await APP.updater.start_polling()
    await APP.updater.wait_for_stop()


if __name__ == "__main__":
    asyncio.run(main())
