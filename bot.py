# bot.py
# Full file - main Telegram bot and grid loop orchestrator.

import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
import grid_engine
from functools import partial
import time

# configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    level=logging.DEBUG if config.VERBOSE else logging.INFO,
)
log = logging.getLogger("tg_bot")

# global state
GRID_TASKS = {}  # symbol -> asyncio.Task
RUNNING = False
EXCHANGE = None

# Helper to send messages safely
async def send_safe(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str):
    try:
        await context.bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        log.exception("Failed to send message to chat %s: %s", chat_id, e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUNNING, EXCHANGE
    chat_id = update.effective_chat.id
    if RUNNING:
        await send_safe(context, chat_id, "BOT ALREADY RUNNING")
        return

    # init exchange
    try:
        # create exchange sync instance inside to_thread to avoid blocking the loop
        EXCHANGE = await asyncio.to_thread(grid_engine.get_exchange)
    except Exception as e:
        log.exception("Exchange init failed")
        await send_safe(context, chat_id, f"❌ Exchange init failed: {e}")
        return

    RUNNING = True
    await send_safe(context, chat_id, f"BOT STARTED — GRID RUNNING\nPairs: {', '.join(config.PAIRS)}")
    # start a grid task per pair
    for pair in config.PAIRS:
        pair = pair.strip()
        if not pair:
            continue
        # create and store a task
        t = asyncio.create_task(grid_loop(pair, update, context))
        GRID_TASKS[pair] = t
        await asyncio.sleep(0.1)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUNNING, GRID_TASKS
    chat_id = update.effective_chat.id
    if not RUNNING:
        await send_safe(context, chat_id, "BOT NOT RUNNING")
        return
    # cancel tasks
    for sym, task in list(GRID_TASKS.items()):
        task.cancel()
    GRID_TASKS = {}
    RUNNING = False
    await send_safe(context, chat_id, "BOT STOPPED")

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    One-shot scan: fetch balance and prices and reply
    """
    chat_id = update.effective_chat.id
    # ensure exchange available
    try:
        exchange = await asyncio.to_thread(grid_engine.get_exchange)
    except Exception as e:
        log.exception("scan - exchange init failed")
        await send_safe(context, chat_id, f"SCAN ERROR: exchange init failed: {e}")
        return

    # fetch balance
    try:
        bal = await asyncio.to_thread(grid_engine.get_assumed_balance, exchange, config.QUOTE_ASSET)
        bal = float(bal or 0.0)
    except Exception as e:
        log.exception("scan balance error")
        await send_safe(context, chat_id, f"SCAN ERROR: {e}")
        return

    text_lines = [f"SCAN DEBUG — BALANCE: {bal:.2f} {config.QUOTE_ASSET}"]
    for pair in config.PAIRS:
        p = pair.strip()
        price = await asyncio.to_thread(grid_engine.fetch_price, exchange, p)
        if not price:
            text_lines.append(f"{p}: price=N/A")
            continue
        # simple hold / neutral logic: not an AI decision — user will refine later
        text_lines.append(f"{p}: price={price:.6f}\n{p}: HOLD — Neutral zone")
    await send_safe(context, chat_id, "\n\n".join(text_lines))

async def grid_loop(symbol: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Single-symbol loop. Synchronous exchange calls occur inside asyncio.to_thread.
    This does:
      - fetch price
      - fetch balance
      - compute amount
      - if conditions met, execute market order
    """
    chat_id = update.effective_chat.id
    exchange = EXCHANGE or await asyncio.to_thread(grid_engine.get_exchange)
    log.info("Grid loop starting for %s", symbol)
    try:
        while True:
            try:
                # fetch balance (quote asset)
                bal = await asyncio.to_thread(grid_engine.get_assumed_balance, exchange, config.QUOTE_ASSET)
                bal = float(bal or 0.0)
                # fetch price
                price = await asyncio.to_thread(grid_engine.fetch_price, exchange, symbol)
                if price is None or price == 0:
                    await send_safe(context, chat_id, f"[GRID] {symbol} — price N/A")
                    await asyncio.sleep(config.GRID_LOOP_SECONDS)
                    continue

                # decide whether to place an order — this is a placeholder "neutral-grid" logic:
                # If we have enough balance, try a single long entry as a sample.
                # You should replace this with your own entry logic later.
                amount = grid_engine.calculate_amount_for_market(bal, price, allocation=config.ALLOCATION_PER_PAIR, leverage=config.LEVERAGE)
                # check min order using cost in quote currency
                cost_estimate = amount * price
                if bal < float(config.MIN_ORDER):
                    # not enough balance to trade
                    log.info("Balance too small for %s: %s", symbol, bal)
                    await send_safe(context, chat_id, f"[GRID] {symbol} — NO ORDER @ {price:.4f}\nBalance {bal:.2f} too small")
                else:
                    # Demo entry condition: if price changed by more than X% (placeholder)
                    # For now we will not spam orders: only place if amount >= tiny threshold
                    if amount > 0 and cost_estimate >= float(config.MIN_ORDER):
                        # Place a sample LONG market entry once (demo): to avoid repeated entries, we'll place only if
                        # certain simple condition is met (e.g., price last digit ends with something) - this prevents continuous buys.
                        # Replace this with your real signal detection logic.
                        # For demo: compute a stable hash-like check to avoid repeated orders:
                        sig = int(time.time() / 600)  # change every 10 minutes
                        if (hash(symbol) + sig) % 13 == 0:  # rare-ish event
                            try:
                                result = await asyncio.to_thread(grid_engine.execute_order, exchange, symbol, "buy", amount, None, "market")
                                await send_safe(context, chat_id, f"[GRID] {symbol} — LONG_ENTRY @ {price:.6f}\nORDER RESULT: {result}")
                            except Exception as e:
                                log.exception("Order error for %s", symbol)
                                await send_safe(context, chat_id, f"ORDER ERROR: {e}")
                        else:
                            # No order this loop — show neutral / hold status
                            await send_safe(context, chat_id, f"[GRID] {symbol} — HOLD — Neutral zone")
                    else:
                        await send_safe(context, chat_id, f"[GRID] {symbol} — NO ORDER @ {price:.4f}\nBalance {bal:.2f} too small or amount {amount:.6f}")
                await asyncio.sleep(config.GRID_LOOP_SECONDS)
            except asyncio.CancelledError:
                log.info("Grid loop cancelled for %s", symbol)
                break
            except Exception as e:
                log.exception("Unhandled error in grid_loop for %s: %s", symbol, e)
                await send_safe(context, chat_id, f"[GRID LOOP ERROR] {e}")
                # backoff a bit on errors
                await asyncio.sleep(max(5, config.GRID_LOOP_SECONDS))
    finally:
        log.info("Exiting grid loop for %s", symbol)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await send_safe(context, chat_id, f"RUNNING: {RUNNING}\nTasks: {list(GRID_TASKS.keys())}")

def main():
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in config/env")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("status", status))

    # run app
    app.run_polling()

if __name__ == "__main__":
    main()
