# bot.py  (FULL replacement)
import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
import grid_engine
import config
import telegram

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xlr8-bot")

# -----------------------
# HELPERS
# -----------------------
async def safe_send(update_or_bot, chat_id, text):
    try:
        if isinstance(update_or_bot, Update):
            await update_or_bot.message.reply_text(text)
        else:
            await update_or_bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        # log only
        logger.exception("send error: %s", e)

# -----------------------
# /scan handler
# -----------------------
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        exchange = await grid_engine.get_exchange()
        balance = await grid_engine.get_balance(exchange)
        await update.message.reply_text(f"SCAN DEBUG — BALANCE: {balance:.2f} USDT\nCONFIG_VERSION: {config.CONFIG_VERSION}")

        for pair in config.PAIRS:
            info = await grid_engine.process_symbol(exchange, pair, balance)
            await update.message.reply_text(f"{pair}: {info['action']} — {info['result']}")
    except Exception as e:
        await update.message.reply_text(f"SCAN ERROR:\n{str(e)}")
        logger.exception("scan error")

# -----------------------
# grid_loop job (run_repeating target)
# -----------------------
async def grid_loop(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.chat_data.get("chat_id")
    if not chat_id:
        # nothing to do
        return
    try:
        exchange = await grid_engine.get_exchange()
        balance = await grid_engine.get_balance(exchange)

        for pair in config.PAIRS:
            info = await grid_engine.process_symbol(exchange, pair, balance)
            msg = f"[GRID] {pair} — {info['action']} @ {info['price']}\n{info['result']}"
            await context.bot.send_message(chat_id=chat_id, text=msg)

    except telegram.error.Conflict as ce:
        # another instance is using getUpdates — tell user
        await context.bot.send_message(chat_id=chat_id, text="ERROR: Bot conflict — multiple instances running. Stop other instances.")
        logger.exception("telegram conflict")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"[GRID LOOP ERROR]\n{str(e)}")
        logger.exception("grid loop error")

# -----------------------
# /start handler
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    await update.message.reply_text("BOT STARTED — PIONEX-STYLE NEUTRAL GRID")

    # remove previous jobs with same name
    for job in context.job_queue.get_jobs_by_name("grid_loop"):
        job.schedule_removal()

    # run repeating job
    context.job_queue.run_repeating(
        grid_loop,
        interval=config.GRID_LOOP_SECONDS,
        first=3,
        name="grid_loop",
    )

    # store chat id so job can message
    context.chat_data["chat_id"] = chat_id

# -----------------------
# /stop handler
# -----------------------
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # remove job(s)
    for job in context.job_queue.get_jobs_by_name("grid_loop"):
        job.schedule_removal()
    await update.message.reply_text("GRID STOPPED — JOB REMOVED")

# -----------------------
# MAIN
# -----------------------
def main():
    # Guard: ensure single process not running elsewhere
    # (We cannot forcibly stop other instances; just warn in logs)
    try:
        app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

        app.add_handler(CommandHandler("scan", scan))
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("stop", stop))

        # start polling (synchronous)
        logger.info("Starting bot (run_polling)...")
        app.run_polling()
    except telegram.error.Conflict as ce:
        # If a conflict occurs here, it means another instance is active.
        logger.exception("Telegram Conflict: is another bot instance running?")
        raise
    except Exception:
        logger.exception("Unhandled exception in main")
        raise

if __name__ == "__main__":
    main()

