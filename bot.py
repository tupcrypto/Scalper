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

# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# -------------------------------------------------
# Helper: get assumed balance (no API)
# -------------------------------------------------
def get_bot_balance() -> float:
    return float(config.ASSUMED_BALANCE_USDT)


# -------------------------------------------------
# /scan command
# -------------------------------------------------
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = get_bot_balance()
    lines = [f"SCAN DEBUG — BALANCE: {balance} USDT"]

    for pair in config.PAIRS:
        try:
            price = bitget_api.get_price(pair)
            decision = grid_engine.check_grid_signal(pair, price, balance)
            lines.append(f"{pair}: price={price}")
            lines.append(f"{pair}: {decision}")
        except Exception as e:
            lines.append(f"{pair}: SCAN ERROR: {e}")

    await update.message.reply_text("\n".join(lines))


# -------------------------------------------------
# Background grid job (runs every N seconds)
# -------------------------------------------------
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


# -------------------------------------------------
# /start command – schedule job
# -------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Avoid double-scheduling
    existing = context.job_queue.get_jobs_by_name("grid_loop")
    if existing:
        await update.message.reply_text("⚠️ Bot already running.")
        return

    # Schedule repeating job: every 20s, first run after 5s
    context.job_queue.run_repeating(
        grid_job, interval=20, first=5, name="grid_loop"
    )

    logger.info("Grid job scheduled (every 20 seconds).")
    await update.message.reply_text("🚀 BOT STARTED AND AUTO GRID LOOP SCHEDULED…")


# -------------------------------------------------
# /stop command – cancel job
# -------------------------------------------------
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jobs = context.job_queue.get_jobs_by_name("grid_loop")
    for job in jobs:
        job.schedule_removal()

    logger.info("Grid job stopped.")
    await update.message.reply_text("🛑 BOT STOPPED.")


# -------------------------------------------------
# Main runner
# -------------------------------------------------
def main():
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    logger.info("Starting bot polling…")
    app.run_polling()


if __name__ == "__main__":
    main()
