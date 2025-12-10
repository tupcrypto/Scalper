import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
import grid_engine
import config

# ========================================================
# GLOBAL EXCHANGE INSTANCE (IMPORTANT)
# ========================================================
exchange = grid_engine.get_exchange()


# ========================================================
# /start HANDLER
# ========================================================
async def start(update, context):
    await update.message.reply_text("BOT STARTED — PIONEX-STYLE NEUTRAL GRID")

    while True:
        try:
            balance = await grid_engine.get_balance(exchange)

            # Process all configured pairs
            for symbol in config.PAIRS:
                result = await grid_engine.trade_symbol(exchange, symbol, balance)

                msg = (
                    f"[GRID] {symbol} — {result['action']} @ {result['price']}\n"
                    f"{result['result']}"
                )

                await update.message.reply_text(msg)

            # loop delay
            await asyncio.sleep(config.GRID_LOOP_SECONDS)

        except Exception as e:
            await update.message.reply_text(f"[GRID LOOP ERROR]\n{str(e)}")
            await asyncio.sleep(10)


# ========================================================
# /scan HANDLER
# ========================================================
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


# ========================================================
# MAIN APPLICATION
# ========================================================
async def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    # start bot and never close event loop manually
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())

