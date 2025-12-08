import asyncio
import config
import bitget_api

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


# -------------------------------------------------
# TELEGRAM BOT APP
# -------------------------------------------------
application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()


# -------------------------------------------------
# /start
# -------------------------------------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.GRID_ACTIVE = True
    await update.message.reply_text("🚀 BOT STARTED — Auto scan loop ON")
    asyncio.create_task(auto_loop())


# -------------------------------------------------
# /stop
# -------------------------------------------------
async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.GRID_ACTIVE = False
    await update.message.reply_text("🛑 BOT STOPPED")


# -------------------------------------------------
# /scan  — REAL DEBUG MODE
# SHOWS:
# 1) RAW FUTURES BALANCE OBJECT
# 2) PARSED BALANCE
# 3) PRICE PER PAIR
# -------------------------------------------------
async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 1️⃣ Connect to Bitget
    try:
        exchange = bitget_api.get_exchange()
    except Exception as e:
        await update.message.reply_text(f"❌ EXCHANGE INIT ERROR:\n{e}")
        return

    # 2️⃣ RAW FUTURES BALANCE OBJECT
    try:
        raw_balance = exchange.fetch_balance({"type": "swap"})
    except Exception as e:
        await update.message.reply_text(f"❌ RAW BALANCE ERROR:\n{e}")
        return

    # Send raw structure (trim for Telegram)
    pretty = str(raw_balance)[:3500]
    await update.message.reply_text(
        "📦 RAW BITGET FUTURES BALANCE OBJECT:\n\n" + pretty
    )

    # 3️⃣ PARSED BALANCE (still zero until parser fixed)
    try:
        bal = bitget_api.get_usdt_balance(exchange)
    except:
        bal = 0

    msg = [f"🟡 Parsed Balance = {bal}"]

    for pair in config.PAIRS:
        try:
            price = bitget_api.get_price(exchange, pair)
        except:
            price = 0

        msg.append(f"{pair}: price={price}")

    await update.message.reply_text("\n".join(msg))


# -------------------------------------------------
# AUTO LOOP
# -------------------------------------------------
async def auto_loop():
    await asyncio.sleep(3)

    while True:
        if not config.GRID_ACTIVE:
            await asyncio.sleep(10)
            continue

        try:
            exchange = bitget_api.get_exchange()

            for pair in config.PAIRS:
                price = bitget_api.get_price(exchange, pair)
                print(f"[AUTO] {pair}: price={price}")

        except Exception as e:
            print("[AUTO LOOP ERROR]:", e)

        await asyncio.sleep(120)   # 2 min


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    # IMPORTANT — we use CommandHandler, not decorators
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("stop", stop_cmd))
    application.add_handler(CommandHandler("scan", scan_cmd))

    print("🤖 Telegram bot is LIVE (polling)")
    application.run_polling(stop_signals=None)


if __name__ == "__main__":
    main()
