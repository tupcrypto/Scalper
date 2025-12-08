import os
import asyncio
import ccxt
import logging
from telegram.ext import ApplicationBuilder, CommandHandler
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import config
import grid_engine

logging.basicConfig(level=logging.INFO)

# --------------------------------------------------------------------------------
# PORT SERVER FOR RENDER
# --------------------------------------------------------------------------------
PORT = int(os.getenv("PORT", 8080))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"BOT IS RUNNING")
        
def start_port_server():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()

threading.Thread(target=start_port_server).start()


# --------------------------------------------------------------------------------
# TELEGRAM + EXCHANGE INITIALIZER
# --------------------------------------------------------------------------------
_exchange = None
_lock = asyncio.Lock()             # Prevent polling conflict


def get_exchange():
    global _exchange
    if _exchange:
        return _exchange

    _exchange = ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_API_PASSPHRASE,
        "enableRateLimit": True,
        "options": {"defaultType": "swap"}
    })
    return _exchange


async def get_balance():
    ex = get_exchange()
    try:
        bal = await asyncio.to_thread(ex.fetch_balance)
        return float(bal["USDT"]["free"])
    except Exception as e:
        logging.error(f"BALANCE ERROR: {e}")
        return 0.0


# --------------------------------------------------------------------------------
# GRID LOOP — LIVE MODE
# --------------------------------------------------------------------------------
async def grid_loop(app):
    global _lock
    async with _lock:      # prevent multiple loops
        await app.bot.send_message(config.ADMIN_CHAT_ID, "GRID LOOP STARTED…")

    while True:
        try:
            bal = await get_balance()
            for pair in config.PAIRS:
                price = await asyncio.to_thread(get_exchange().fetch_ticker, pair)
                price = float(price["last"])

                action = grid_engine.check_grid_signal(price, bal)

                if action == "BUY":
                    await app.bot.send_message(config.ADMIN_CHAT_ID,
                        f"BUY SIGNAL for {pair} @ {price}")
                    # PLACE ORDER LATER

                elif action == "SELL":
                    await app.bot.send_message(config.ADMIN_CHAT_ID,
                        f"SELL SIGNAL for {pair} @ {price}")
                    # PLACE ORDER LATER

        except Exception as e:
            await app.bot.send_message(config.ADMIN_CHAT_ID,
                f"[GRID ERROR] {e}")

        await asyncio.sleep(10)


# --------------------------------------------------------------------------------
# /start COMMAND
# --------------------------------------------------------------------------------
async def start(update, context):
    await context.bot.send_message(update.effective_chat.id,
        "BOT STARTED — AGGRESSIVE GRID MODE")

    app = context.application
    asyncio.create_task(grid_loop(app))


# --------------------------------------------------------------------------------
# /scan COMMAND
# --------------------------------------------------------------------------------
async def scan(update, context):
    try:
        bal = await get_balance()
        reply = f"SCAN DEBUG — BALANCE: {bal} USDT\n"

        for pair in config.PAIRS:
            tick = await asyncio.to_thread(get_exchange().fetch_ticker, pair)
            price = float(tick["last"])
            reply += f"{pair}: price={price}\n"

        await context.bot.send_message(update.effective_chat.id, reply)

    except Exception as e:
        await context.bot.send_message(update.effective_chat.id,
            f"SCAN ERROR: {e}")


# --------------------------------------------------------------------------------
# MAIN APP
# --------------------------------------------------------------------------------
async def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
