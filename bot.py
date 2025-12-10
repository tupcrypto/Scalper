from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

import config
import grid_engine


# ------------------------------------
# GLOBAL EXCHANGE
# ------------------------------------
exchange = grid_engine.get_exchange(
    config.BITGET_API_KEY,
    config.BITGET_API_SECRET,
    config.BITGET_PASSPHRASE
)


# ------------------------------------
# SCAN COMMAND
# ------------------------------------
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        balance = float(exchange.fetch_balance()['USDT']['free'])

        reply = f"SCAN DEBUG — BALANCE: {balance:.2f} USDT\n\n"

        for symbol in config.PAIRS:
            info = grid_engine.trade_symbol(exchange, symbol, balance)
            reply += (
                f"{symbol}: price={info['price']}\n"
                f"{symbol}: {info['action']} — {info['result']}\n\n"
            )

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"SCAN ERROR:\n{str(e)}")


# ------------------------------------
# GRID LOOP
# ------------------------------------
async def grid_loop(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.chat_data.get("chat_id")
    if not chat_id:
        return

    try:
        balance = float(exchange.fetch_balance()['USDT']['free'])

        for symbol in config.PAIRS:
            info = grid_engine.trade_symbol(exchange, symbol, balance)

            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"[GRID] {symbol} — {info['action']} @ {info['price']}\n"
                    f"{info['result']}"
                )
            )

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"[GRID LOOP ERROR]\n{str(e)}"
        )


# ------------------------------------
# START COMMAND
# ------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id

    await update.message.reply_text("BOT STARTED — PIONEX-STYLE NEUTRAL GRID")

    for job in context.job_queue.get_jobs_by_name("grid_loop"):
        job.schedule_removal()

    context.job_queue.run_repeating(
        grid_loop,
        interval=90,
        first=5,
        name="grid_loop",
    )

    # save chat ID for grid loop
    context.chat_data["chat_id"] = chat_id


# ------------------------------------
# MAIN APP (NO ASYNCIO.RUN)
# ------------------------------------
if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("start", start))

    app.job_queue

    app.run_polling()

