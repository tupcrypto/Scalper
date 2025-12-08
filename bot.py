# ==========================================
# bot.py  (FULL FILE)
# ==========================================

import os
import asyncio
import threading
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

import ccxt
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

import config
import grid_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# Tiny HTTP server so Render web service sees an open port
# -------------------------------------------------------------
PORT = int(os.getenv("PORT", "8080"))

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"XLR8 GRID BOT RUNNING")

def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()

# Start health server in background thread
threading.Thread(target=start_health_server, daemon=True).start()

# -------------------------------------------------------------
# Exchange init (Bitget USDT-M Futures)
# -------------------------------------------------------------
_exchange = None

def get_exchange():
    global _exchange
    if _exchange is not None:
        return _exchange

    _exchange = ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_API_PASSPHRASE,
        "enableRateLimit": True,
        "options": {"defaultType": "swap"}  # USDT-M perpetual
    })
    return _exchange

# -------------------------------------------------------------
# Futures balance (USDT-M)
# -------------------------------------------------------------
async def get_balance() -> float:
    ex = get_exchange()
    try:
        # IMPORTANT: type="swap" -> futures
        bal = await asyncio.to_thread(ex.fetch_balance, {"type": "swap"})

        # Common Bitget futures pattern
        if "USDT" in bal and "free" in bal["USDT"]:
            return float(bal["USDT"]["free"])

        # fallback to total field if needed
        if "USDT" in bal and "total" in bal["USDT"]:
            return float(bal["USDT"]["total"])

        logger.warning(f"Unknown balance format: {bal}")
        return 0.0
    except Exception as e:
        logger.error(f"RAW BALANCE ERROR: {e}")
        return 0.0

# -------------------------------------------------------------
# /scan command
# -------------------------------------------------------------
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    balance = await get_balance()
    msg_lines = [f"SCAN DEBUG — BALANCE: {balance:.2f} USDT"]

    ex = get_exchange()

    for pair in config.PAIRS:
        try:
            ticker = await asyncio.to_thread(ex.fetch_ticker, pair)
            price = float(ticker["last"])

            decision = grid_engine.check_grid_signal(price, balance)

            msg_lines.append("")
            msg_lines.append(f"{pair}: price={price}")
            msg_lines.append(
                f"{pair}: {decision['action']} — {decision['reason']}"
            )
        except Exception as e:
            msg_lines.append(f"{pair}: ERROR — {e}")

    await context.bot.send_message(chat_id=chat_id, text="\n".join(msg_lines))

# -------------------------------------------------------------
# Grid loop job (called by JobQueue)
# -------------------------------------------------------------
async def grid_job(context: ContextTypes.DEFAULT_TYPE):
    ex = get_exchange()
    balance = await get_balance()

    for pair in config.PAIRS:
        try:
            ticker = await asyncio.to_thread(ex.fetch_ticker, pair)
            price = float(ticker["last"])

            decision = grid_engine.check_grid_signal(price, balance)

            if decision["action"] == "HOLD":
                continue  # no trade

            qty = float(decision["amount"])
            if qty <= 0:
                continue

            text = [
                "🔁 GRID SIGNAL",
                f"Pair: {pair}",
                f"Action: {decision['action']}",
                f"Qty: {qty}",
                f"Reason: {decision['reason']}",
            ]

            # Place orders only if LIVE_TRADING is enabled
            if config.LIVE_TRADING:
                side = "buy" if decision["action"] == "BUY" else "sell"
                try:
                    await asyncio.to_thread(
                        ex.create_market_order,
                        pair,
                        side,
                        qty
                    )
                    text.append("Order: EXECUTED ✅")
                except Exception as oe:
                    text.append(f"Order ERROR: {oe}")
            else:
                text.append("Order: SIMULATION ONLY (LIVE_TRADING=0)")

            # Push notification to your chat if configured
            target_chat = (
                int(config.TELEGRAM_CHAT_ID)
                if config.TELEGRAM_CHAT_ID
                else None
            )
            if target_chat:
                await context.bot.send_message(
                    chat_id=target_chat,
                    text="\n".join(text),
                )

        except Exception as e:
            target_chat = (
                int(config.TELEGRAM_CHAT_ID)
                if config.TELEGRAM_CHAT_ID
                else None
            )
            if target_chat:
                await context.bot.send_message(
                    chat_id=target_chat,
                    text=f"[GRID LOOP ERROR] {pair}: {e}",
                )
            logger.error(f"GRID LOOP ERROR for {pair}: {e}")

# -------------------------------------------------------------
# /start command
# -------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Ensure grid job is scheduled only once
    jobs = context.job_queue.get_jobs_by_name("grid_loop")
    if not jobs:
        context.job_queue.run_repeating(
            grid_job,
            interval=30,    # every 30s (aggressive)
            first=0,
            name="grid_loop",
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text="BOT STARTED — AGGRESSIVE MODE\nGrid loop: ON (30s)",
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Grid loop is already running.",
        )

# -------------------------------------------------------------
# Main entry
# -------------------------------------------------------------
async def main():
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("scan", scan))
    application.add_handler(CommandHandler("start", start))

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

