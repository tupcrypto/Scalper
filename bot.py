"""
Full bot.py — single file to deploy.
Supports /start, /stop, /scan. Uses grid_engine for exchange operations.
"""
import logging
import asyncio
import os
from functools import partial
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
import grid_engine

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("tgbot")

# Read Toobit credentials from config (env)
API_KEY = config.TOOBIT_API_KEY
API_SECRET = config.TOOBIT_API_SECRET

# Globals
_app = None
_grid_job = None
_exchange = None
_grid_running = False


async def get_exchange_async():
    # run blocking ccxt creation in executor
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(grid_engine.get_exchange, API_KEY, API_SECRET))


async def fetch_balance_async(exchange):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(grid_engine.fetch_usdt_futures_balance, exchange))


async def compute_amount_async(exchange, symbol, usdt_budget, leverage):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(grid_engine.compute_order_amount, exchange, symbol, usdt_budget, leverage))


async def place_order_async(exchange, symbol, side, amount):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(grid_engine.place_market_order, exchange, symbol, side, amount))


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _grid_running, _grid_job, _exchange
    user = update.effective_user
    logger.info("Start command from %s", user.id)
    if not _exchange:
        try:
            _exchange = await get_exchange_async()
            # attempt to load markets
            await asyncio.get_event_loop().run_in_executor(None, _exchange.load_markets)
        except Exception as e:
            msg = f"❌ EXCHANGE INIT ERROR: {e}"
            logger.exception(msg)
            await update.message.reply_text(msg)
            return

    if _grid_running:
        await update.message.reply_text("Bot already running.")
        return

    _grid_running = True
    await update.message.reply_text(f"BOT STARTED — {config.MODE} MODE")

    # create job repeating
    jq = context.application.job_queue
    # run every GRID_LOOP_SECONDS
    _grid_job = jq.run_repeating(grid_loop, interval=config.GRID_LOOP_SECONDS, first=0, name="grid_loop")
    logger.info("Grid job scheduled every %s seconds", config.GRID_LOOP_SECONDS)


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _grid_running, _grid_job
    if not _grid_running:
        await update.message.reply_text("Bot is not running.")
        return
    if _grid_job:
        _grid_job.schedule_removal()
        _grid_job = None
    _grid_running = False
    await update.message.reply_text("Bot stopped.")


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _exchange
    if not _exchange:
        try:
            _exchange = await get_exchange_async()
            await asyncio.get_event_loop().run_in_executor(None, _exchange.load_markets)
        except Exception as e:
            msg = f"❌ EXCHANGE INIT ERROR: {e}"
            logger.exception(msg)
            await update.message.reply_text(msg)
            return

    # get available USDT balance
    try:
        bal = await fetch_balance_async(_exchange)
    except Exception as e:
        msg = f"❌ RAW BALANCE ERROR:\n{e}"
        logger.exception(msg)
        await update.message.reply_text(msg)
        return

    msg_lines = [f"SCAN DEBUG — BALANCE: {bal:.2f} USDT"]
    for s in config.PAIRS:
        sym = s.strip()
        try:
            ticker = await asyncio.get_event_loop().run_in_executor(None, partial(_exchange.fetch_ticker, sym))
            price = float(ticker.get("last") or ticker.get("close") or ticker.get("bid") or ticker.get("ask"))
            # Very simple rule: if price changed > 1% we print action else hold
            msg_lines.append(f"{sym}: price={price:.4f}")
            # no trading here; just report
        except Exception as e:
            msg_lines.append(f"{sym}: ERROR fetching ticker: {e}")

    await update.message.reply_text("\n".join(msg_lines))


async def grid_loop(context: ContextTypes.DEFAULT_TYPE):
    """
    This runs in the background by JobQueue.
    It will check each symbol and try to place a single market entry if budget and conditions met.
    """
    global _exchange
    job = context.job
    logger.debug("Grid loop tick")
    if not _exchange:
        try:
            _exchange = await get_exchange_async()
            await asyncio.get_event_loop().run_in_executor(None, _exchange.load_markets)
        except Exception as e:
            logger.exception("Exchange init in job failed: %s", e)
            await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=f"❌ EXCHANGE INIT ERROR: {e}")
            return

    # 1) fetch available USDT
    try:
        balance = await fetch_balance_async(_exchange)
    except Exception as e:
        logger.exception("Balance fetch failed")
        await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=f"❌ RAW BALANCE ERROR:\n{e}")
        return

    # minimum guard
    if balance < 0.0001:
        await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=f"SCAN DEBUG — BALANCE: {balance:.2f} USDT\nNo usable balance.")
        return

    # per-symbol allocation
    symbols = [p.strip() for p in config.PAIRS]
    per_sym_budget = (balance * (config.MAX_CAPITAL_PCT / 100)) / max(1, len(symbols))

    for sym in symbols:
        try:
            ticker = await asyncio.get_event_loop().run_in_executor(None, partial(_exchange.fetch_ticker, sym))
            price = float(ticker.get("last") or ticker.get("close") or ticker.get("ask") or ticker.get("bid"))
        except Exception as e:
            logger.exception("ticker fetch failed for %s", sym)
            await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=f"{sym}: ticker fetch error: {e}")
            continue

        if per_sym_budget < config.MIN_ORDER_USDT:
            await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID,
                                           text=f"[GRID] {sym} — NO ORDER @ {price}\nBalance {balance:.2f} too small (per-symbol budget {per_sym_budget:.2f})")
            continue

        # Compute order amount in base currency
        try:
            amount = await compute_amount_async(_exchange, sym, per_sym_budget, config.LEVERAGE)
            if amount <= 0:
                await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID,
                                               text=f"[GRID] {sym} — NO ORDER @ {price}\ncomputed amount 0 (per_sym_budget {per_sym_budget})")
                continue
        except Exception as e:
            logger.exception("compute amount failed")
            await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=f"[GRID] {sym} — ERROR computing amount: {e}")
            continue

        # Simple neutral logic: place long if price dropped slightly (this is placeholder logic)
        # For production: replace with real entry logic (reversals, S/R, indicators)
        # Here we alternate long/short quickly as demo — choose long for now
        side = "buy"

        # Announce
        await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID,
                                       text=f"[GRID] {sym} — {side.upper()}_ENTRY @ {price:.4f} — amount={amount}")

        if not config.LIVE_TRADING:
            await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID,
                                           text=f"[SIMULATION] Would place {side} market order {sym} amount={amount}")
            continue

        # Try placing order
        try:
            order = await place_order_async(_exchange, sym, side, amount)
            await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=f"[ORDER] {order}")
        except Exception as e:
            logger.exception("place order failed")
            await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=f"ORDER ERROR: {e}")


def build_app():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("scan", cmd_scan))
    return app


async def main():
    global _app
    _app = build_app()
    logger.info("Starting bot application")
    # run polling — this blocks
    await _app.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("Fatal bot error: %s", e)
