from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio
import grid_engine
import config

# ONE GLOBAL EXCHANGE INSTANCE
exchange = grid_engine.get_exchange()


async def start(update, context):
    await update.message.reply_text("BOT STARTED — PIONEX-STYLE NEUTRAL GRID")

    while True:
        try:
            balance = await grid_engine.get_balance(exchange)

            for symbol in config.PAIRS:
                result = await grid_engine.trade_symbol(exchange, symbol, balance)

                msg = (
                    f"[GRID] {symbol} — {result['action']} @ {result['price']}\n"
                    f"{result['result']}"
                )

                await update.message.reply_text(msg)

            await asyncio.sleep(config.GRID_LOOP_SECONDS)

        except Exception as e:
            await update.message.reply_text(f"[GRID LOOP ERROR]\n{str(e)}")
            await asyncio.sleep(10)


async def scan(update, context):
    try:
        balance = await grid_engine.get_balance(exchange)
        await update.message.reply_text(f"SCAN DEBUG — BALANCE: {balance:.2f} USDT")

        for symbol in config.PAIRS:
            result = await grid_engine.trade_symbol(exchange, symbol, balance)

            msg = (
                f"{symbol}: price={result['price']}\n"
                f"{symbol}: {result['action']} — {result['result']}"
            )

            await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(f"SCAN ERROR:\n{str(e)}")


# ⭐⭐ FIX: NO asyncio.run(), NO manual loop, JUST polling ⭐⭐
def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    # IMPORTANT — synchronous call to polling with no loop closures
    app.run_polling()


if __name__ == "__main__":
    main()

