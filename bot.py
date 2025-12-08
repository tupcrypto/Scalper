import asyncio
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
import config
import ccxt
import grid_engine

logging.basicConfig(level=logging.INFO)

# -----------------------------
# INIT EXCHANGE
# -----------------------------
exchange = ccxt.bitget({
    "apiKey": config.EXCHANGE_API_KEY,
    "secret": config.EXCHANGE_API_SECRET,
    "password": config.EXCHANGE_PASSPHRASE,
    "enableRateLimit": True,
})

# -----------------------------
# CHECK BALANCE
# -----------------------------
async def get_balance():
    try:
        balance = exchange.fetch_balance()
        futures = balance.get("USDT", {})
        free = futures.get("free", 0)
        return round(float(free), 2)
    except Exception as e:
        return f"RAW BALANCE ERROR:\n{e}"

# -----------------------------
# /scan COMMAND
# -----------------------------
async def scan(update, context: ContextTypes.DEFAULT_TYPE):
    bal = await get_balance()
    await update.message.reply_text(f"SCAN DEBUG — BALANCE: {bal} USDT")

    for p in config.PAIRS:
        try:
            ticker = exchange.fetch_ticker(p)
            price = ticker['last']
        except:
            await update.message.reply_text(f"{p}: TICKER ERROR")
            continue

        action = grid_engine.check_grid_signal(price, p)

        await update.message.reply_text(
            f"{p}: price={price}\n{action}"
        )

# -----------------------------
# GRID LOOP
# -----------------------------
async def grid_loop(application):
    while True:
        try:
            for p in config.PAIRS:
                ticker = exchange.fetch_ticker(p)
                price = ticker['last']
                action = grid_engine.check_grid_signal(price, p)

                if "BUY" in action:
                    size = grid_engine.calc_order_size()
                    if config.LIVE_TRADING:
                        exchange.create_market_buy_order(p, size)

                if "SELL" in action:
                    size = grid_engine.calc_order_size()
                    if config.LIVE_TRADING:
                        exchange.create_market_sell_order(p, size)

                # send updates to Telegram
                if config.TELEGRAM_CHAT_ID:
                    await application.bot.send_message(
                        chat_id=config.TELEGRAM_CHAT_ID,
                        text=f"[GRID] {p}: {action}"
                    )

        except Exception as e:
            if config.TELEGRAM_CHAT_ID:
                await application.bot.send_message(
                    chat_id=config.TELEGRAM_CHAT_ID,
                    text=f"[GRID LOOP ERROR]\n{e}"
                )

        await asyncio.sleep(25)  # aggressive mode

# -----------------------------
# /start COMMAND
# -----------------------------
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("BOT STARTED — AGGRESSIVE MODE")

    application = context.application
    asyncio.create_task(grid_loop(application))

# -----------------------------
# /balance COMMAND
# -----------------------------
async def balance(update, context):
    bal = await get_balance()
    await update.message.reply_text(f"BALANCE: {bal} USDT")

# -----------------------------
# MAIN
# -----------------------------
def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("balance", balance))

    app.run_polling()

if __name__ == "__main__":
    main()
