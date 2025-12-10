# =====================================
# BOT.PY — REPLACE FULL FILE
# =====================================

from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio
import config
import grid_engine

exchange = grid_engine.get_exchange()


async def start(update, context):
    await update.message.reply_text("BOT STARTED — PIONEX-STYLE NEUTRAL GRID")

    while True:
        try:
            balance = await grid_engine.get_balance(exchange)

            for symbol in config.PAIRS:
                result = await grid_engine.trade_symbol(exchange, symbol, balance)

                msg = f"[GRID] {symbol} — {result['action']} @ {result['price']}\n{result['result']}"

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

            msg = f"{symbol}: {result['action']} — {result['result']}"
            await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(f"SCAN ERROR:\n{str(e)}")


def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    app.run_polling()


if __name__ == "__main__":
    main()

