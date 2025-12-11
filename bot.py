# bot.py
import os
import asyncio
import logging
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import grid_engine

logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO,
                    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s")
LOG = logging.getLogger("tg_bot")

# Global to hold background task
GRID_TASK: Optional[asyncio.Task] = None
EXCHANGE_INSTANCE = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GRID_TASK, EXCHANGE_INSTANCE
    user = update.effective_user
    LOG.info("/start called by %s", user.username if user else "unknown")

    if GRID_TASK and (not GRID_TASK.done()):
        await update.message.reply_text("Bot already running.")
        return

    # init exchange
    try:
        EXCHANGE_INSTANCE = await grid_engine.get_exchange()
    except Exception as e:
        await update.message.reply_text(f"❌ Exchange init failed: {e}")
        LOG.exception("exchange init")
        return

    # spawn background loop
    GRID_TASK = asyncio.create_task(grid_loop(context))
    await update.message.reply_text(f"BOT STARTED — GRID RUNNING\nPairs: {', '.join(config.PAIRS)}")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GRID_TASK, EXCHANGE_INSTANCE
    LOG.info("/stop called")
    if GRID_TASK:
        GRID_TASK.cancel()
        try:
            await GRID_TASK
        except asyncio.CancelledError:
            pass
        GRID_TASK = None
    # close exchange connection
    if EXCHANGE_INSTANCE:
        try:
            await grid_engine.close_exchange(EXCHANGE_INSTANCE)
        except Exception:
            pass
        EXCHANGE_INSTANCE = None
    await update.message.reply_text("BOT STOPPED — Grid stopped and exchange closed")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # On-demand single scan
    LOG.info("/scan called")
    try:
        exchange = await grid_engine.get_exchange()
        bal = await grid_engine.fetch_usdt_balance(exchange)
        msg = [f"SCAN DEBUG — BALANCE: {bal:.2f} USDT\n"]
        for sym in config.PAIRS:
            price = await grid_engine.fetch_price(exchange, sym)
            if price is None:
                msg.append(f"{sym}: price=N/A")
            else:
                msg.append(f"{sym}: price={price:.6f}")
        await exchange.close()
        await update.message.reply_text("\n".join(msg))
    except Exception as e:
        LOG.exception("scan error")
        await update.message.reply_text(f"SCAN ERROR:\n{e}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # report status
    running = GRID_TASK and (not GRID_TASK.done())
    await update.message.reply_text(f"Grid running: {bool(running)}")

# main grid loop
async def grid_loop(context: ContextTypes.DEFAULT_TYPE):
    """
    Very simple loop per pair:
     - get balance
     - if balance sufficient, compute usdt spend and attempt to place a LIMIT entry order
     - otherwise report HOLD/NO ORDER
    This is a simple example — adapt to your real grid logic.
    """
    global EXCHANGE_INSTANCE
    try:
        if EXCHANGE_INSTANCE is None:
            EXCHANGE_INSTANCE = await grid_engine.get_exchange()
        exchange = EXCHANGE_INSTANCE

        while True:
            try:
                total_usdt = await grid_engine.fetch_usdt_balance(exchange)
                LOG.info("GRID LOOP — BALANCE: %s USDT", total_usdt)
                for sym in config.PAIRS:
                    price = await grid_engine.fetch_price(exchange, sym)
                    if price is None:
                        await notify(context, f"{sym}: price N/A")
                        continue

                    # compute spend
                    spend = grid_engine.compute_usdt_spend(total_usdt)
                    if spend < config.MIN_ORDER_USDT:
                        await notify(context, f"[GRID] {sym} — NO ORDER @ {price:.4f}\nBalance {total_usdt:.2f} too small")
                        continue

                    # Very simple decision: if recent price moved up a bit, hold; else attempt small entry
                    # (Replace with your actual signal logic)
                    # For demo, we will attempt an entry every time if scan-only isn't set
                    if config.SCAN_ONLY:
                        await notify(context, f"[GRID] {sym} — HOLD (scan-only) @ {price:.4f}")
                        continue

                    # calculate limit price with offset for buy
                    buy_price = round(price * (1.0 + config.PRICE_OFFSET_BUY_PCT), 8)
                    sell_price = round(price * (1.0 - config.PRICE_OFFSET_SELL_PCT), 8)

                    try:
                        # attempt a buy limit order using a fraction of spend to avoid big usage
                        per_order_usdt = max(config.MIN_ORDER_USDT, spend * 0.25)
                        order = await grid_engine.place_limit_order(exchange, sym, "buy", per_order_usdt, buy_price)
                        await notify(context, f"[GRID] {sym} — LONG_ENTRY @ {buy_price}\nOrder id: {order.get('id')}")
                    except Exception as e:
                        LOG.exception("Order placement error")
                        await notify(context, f"ORDER ERROR: {e}")

                await asyncio.sleep(config.GRID_LOOP_SECONDS)
            except asyncio.CancelledError:
                LOG.info("grid_loop cancelled")
                break
            except Exception as e:
                LOG.exception("grid loop exception")
                await notify(context, f"[GRID LOOP ERROR]\n{e}")
                await asyncio.sleep(5)
    finally:
        # close exchange on exit
        try:
            if EXCHANGE_INSTANCE:
                await grid_engine.close_exchange(EXCHANGE_INSTANCE)
        except Exception:
            pass

# helper to send messages to owner chat (basic)
async def notify(context: ContextTypes.DEFAULT_TYPE, text: str):
    try:
        # send to the chat that triggered the command if available else do nothing
        # context._chat_id may not be available; safe attempt:
        if context and getattr(context, "application", None):
            # send to bot admin: we don't know owner id; send to last update chat if present
            # fallback: do nothing if not available
            # when grid_loop is started from /start, context contains the chat
            chat_id = None
            # Try to find a chat id in context
            if context.job and context.job.chat_id:
                chat_id = context.job.chat_id
            # fallback: first handler's chat stored in application.bot_data
            chat_id = context.application.bot_data.get("last_chat_id") or chat_id
            if not chat_id:
                # try to use the first chat in update history (best-effort)
                pass
            if chat_id:
                await context.application.bot.send_message(chat_id=chat_id, text=text)
                return
        LOG.info("notify: %s", text)
    except Exception:
        LOG.exception("notify failed")

async def record_last_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # store last chat id so background can notify
    try:
        chat_id = update.effective_chat.id
        context.application.bot_data["last_chat_id"] = chat_id
    except Exception:
        pass

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", config.TELEGRAM_BOT_TOKEN)
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing in env")

    app = ApplicationBuilder().token(token).build()

    # command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("status", status_command))

    # record chat id for notifications
    app.add_handler(CommandHandler("start", record_last_chat))  # also called when /start runs
    app.add_handler(CommandHandler("scan", record_last_chat))
    app.add_handler(CommandHandler("status", record_last_chat))

    LOG.info("==> Running 'python3 bot.py'")
    app.run_polling()  # blocking

if __name__ == "__main__":
    main()
