"""
FINAL WORKING BOT.PY FOR RENDER
- No asyncio.run()
- No manual loop closing
- Uses python-telegram-bot 20.x Application.run_polling()
- Fully compatible with JobQueue
"""

import logging
import asyncio
from functools import partial
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
import grid_engine

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s: %(message)s"
)

logger = logging.getLogger("BOT")

##############################
# GLOBALS
##############################

exchange = None
grid_job = None
grid_running = False


##############################
# EXCHANGE HELPERS (async wrappers)
##############################

async def get_exchange():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        partial(grid_engine.get_exchange, config.TOOBIT_API_KEY, config.TOOBIT_API_SECRET)
    )


async def fetch_balance(ex):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, partial(grid_engine.fetch_usdt_futures_balance, ex)
    )


async def compute_amount(ex, symbol, budget, leverage):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, partial(grid_engine.compute_order_amount, ex, symbol, budget, leverage)
    )


async def place_order(ex, symbol, side, amount):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, partial(grid_engine.place_market_order, ex, symbol, side, amount)
    )


##############################
# COMMAND HANDLERS
##############################

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global exchange, grid_running, grid_job

    if grid_running:
        await update.message.reply_text("Bot already running.")
        return

    # Initialize exchange
    if exchange is None:
        try:
            exchange = await get_exchange()
            await asyncio.get_event_loop().run_in_executor(None, exchange.load_markets)
        except Exception as e:
            msg = f"❌ Exchange init failed: {e}"
            logger.exception(msg)
            await update.message.reply_text(msg)
            return

    grid_running = True
    await update.message.reply_text("BOT STARTED — GRID RUNNING")

    # Start background loop
    grid_job = context.job_queue.run_repeating(
        grid_loop,
        interval=config.GRID_LOOP_SECONDS,
        first=1,
        name="grid_loop"
    )


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global grid_running, grid_job
    if not grid_running:
        await update.message.reply_text("Bot already stopped.")
        return

    grid_running = False
    if grid_job:
        grid_job.schedule_removal()
        grid_job = None

    await update.message.reply_text("Bot stopped.")


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global exchange

    if exchange is None:
        exchange = await get_exchange()
        await asyncio.get_event_loop().run_in_executor(None, exchange.load_markets)

    bal = await fetch_balance(exchange)
    msg = [f"SCAN — Balance: {bal:.2f} USDT"]

    for sym in config.PAIRS:
        try:
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, partial(exchange.fetch_ticker, sym)
            )
            price = float(ticker["last"])
            msg.append(f"{sym}: {price}")
        except Exception as e:
            msg.append(f"{sym}: ERROR {e}")

    await update.message.reply_text("\n".join(msg))


##############################
# GRID LOOP
##############################

async def grid_loop(context: ContextTypes.DEFAULT_TYPE):
    global exchange, grid_running

    if not grid_running:
        return

    if exchange is None:
        exchange = await get_exchange()
        await asyncio.get_event_loop().run_in_executor(None, exchange.load_markets)

    # Fetch balance
    balance = await fetch_balance(exchange)

    symbols = config.PAIRS
    per_budget = (balance * (config.MAX_CAPITAL_PCT / 100)) / len(symbols)

    for sym in symbols:
        try:
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, partial(exchange.fetch_ticker, sym)
            )
            price = float(ticker["last"])
        except Exception as e:
            await context.bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=f"[GRID] {sym} — ticker error {e}"
            )
            continue

        if per_budget < config.MIN_ORDER_USDT:
            await context.bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=f"[GRID] {sym} — NO ORDER @ {price} (budget too small)"
            )
            continue

        # Compute amount
        try:
            amount = await compute_amount(exchange, sym, per_budget, config.LEVERAGE)
        except Exception as e:
            await context.bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=f"[GRID] {sym} — amount error {e}"
            )
            continue

        # Example logic: always BUY for now
        side = "buy"

        await context.bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=f"[GRID] {sym} — BUY ENTRY @ {price} amount={amount}"
        )

        if not config.LIVE_TRADING:
            await context.bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=f"[SIMULATION] Would buy {amount} {sym}"
            )
            continue

        # Execute order
        try:
            order = await place_order(exchange, sym, side, amount)
            await context.bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=f"ORDER EXECUTED:\n{order}"
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=f"ORDER ERROR: {e}"
            )


##############################
# ENTRYPOINT (NO ASYNCIO.RUN)
##############################

def main():
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("stop", cmd_stop))
    application.add_handler(CommandHandler("scan", cmd_scan))

    logger.info("BOT IS RUNNING...")
    application.run_polling()


if __name__ == "__main__":
    main()
