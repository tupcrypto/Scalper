from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio
import config
import grid_engine

GLOBAL_STOP = False  # runtime flag


# ------------------------------
# START COMMAND - GRID LOOP
# ------------------------------
async def start(update, context):
    global GLOBAL_STOP
    GLOBAL_STOP = False

    await update.message.reply_text("BOT STARTED — GRID RUNNING")

    while not GLOBAL_STOP:
        try:
            exchange = await grid_engine.get_exchange()
            balance = await grid_engine.get_balance(exchange)

            # --- Loop all pairs ---
            for symbol in config.PAIRS:
                result = await grid_engine.process_symbol(exchange, symbol, balance)

                msg = f"[GRID] {symbol} — {result['action']} @ {result['price']}\n{result['result']}"
                await update.message.reply_text(msg)

            await asyncio.sleep(config.GRID_LOOP_SECONDS)

        except Exception as e:
            await update.message.reply_text(f"[GRID LOOP ERROR]\n{str(e)}")
            await asyncio.sleep(5)


# ------------------------------
# SCAN COMMAND
# ------------------------------
async def scan(update, context):
    try:
        exchange = await grid_engine.get_exchange()
        balance = await grid_engine.get_balance(exchange)
        await update.message.reply_text(f"SCAN BALANCE: {balance:.2f} USDT")

    except Exception as e:
        await update.message.reply_text(f"SCAN ERROR:\n{str(e)}")


# ------------------------------
# STOP COMMAND
# ------------------------------
async def stop(update, context):
    global GLOBAL_STOP
    GLOBAL_STOP = True
    await update.message.reply_text("GRID STOPPED — NO MORE ORDERS")


# ------------------------------
# MAIN
# ------------------------------
def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("stop", stop))

    app.run_polling()


if __name__ == "__main__":
    main()

