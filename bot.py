import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import config
import bitget_api
import grid_engine

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --------------------------------------------
# Safe internal balance (no API)
# --------------------------------------------
def get_bot_balance() -> float:
    return float(config.ASSUMED_BALANCE_USDT)


# --------------------------------------------
# /scan command — manual check
# --------------------------------------------
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = get_bot_balance()
    lines = [f"SCAN DEBUG — BALANCE: {balance} USDT"]

    for pair in config.PAIRS:
        try:
            price = bitget_api.get_price(pair)
            action = grid_engine.check_grid_signal(pair, price, balance)
            lines.append(f"{pair}: price={price}")
            lines.append(f"{pair}: {action}")
        except Exception as e:
            lines.append(f"{pair}: ERROR: {e}")

    await update.message.reply_text("\n".join(lines))


# --------------------------------------------
# Background job — executes automatically
# --------------------------------------------
async def grid_job(context: ContextTypes.DEFAULT_TYPE):
    balance = get_bot_balance()

    for pair in config.PAIRS:
        try:
            price = bitget_api.get_price(pair)
            decision = grid_engine.check_grid_signal(pair, price, balance)
            logger.info(f"[GRID] {pair} price={price} decision={decision}")

            if config.LIVE_TRADING:
                grid_engine.execute_if_needed(pair, price, balance)

        except Exception as e:
            logger.error(f"[GRID] {pair} error: {e}")


# --------------------------------------------
# /start command — schedules repeating job
# --------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jq = context.application.job_queue   # IMPORTANT FIX

    # avoid double scheduling
    jobs = jq.get_jobs_by_name("grid_loop")
    if jobs:
        await update.message.reply_text("⚠️ Auto loop already running…")
        return

    # RUN EVERY 20 SECONDS
    jq.run_repeating(
        grid_job,
        interval=20,
        first=5,
        name="grid_loop"
    )

    logger.info("Grid job scheduled (every 20 seconds)")
    await update.message.reply_text("🚀 BOT STARTED — AUTO LOOP ACTIVE")


# --------------------------------------------
# /stop — stop grid loop
# --------------------------------------------
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jq = context.application.job_queue

    jobs = jq.get_jobs_by_name("grid_loop")
    for job in jobs:
        job.schedule_removal()

    await update.message.reply_text("🛑 BOT STOPPED")


# --------------------------------------------
# MAIN RUNNER — ensure job queue enabled
# --------------------------------------------
def main():
    app = Application.builder() \
        .token(config.TELEGRAM_BOT_TOKEN) \
        .concurrent_updates(True) \
        .build()

    # VERY IMPORTANT: this initializes the job queue
    jq = app.job_queue

    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    logger.info("Starting polling…")
    app.run_polling()


if __name__ == "__main__":
    main()
