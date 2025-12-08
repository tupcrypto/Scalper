import asyncio
import time
import config
import bitget_api

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ----------------------------------------------------------------------
# TELEGRAM APP
# ----------------------------------------------------------------------
application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

# ----------------------------------------------------------------------
# /start — start grid engine loop (no auto trading yet)
# ----------------------------------------------------------------------
@application.command("start")
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.GRID_ACTIVE = True
    await update.message.reply_text("🚀 BOT STARTED — Auto scan looping every 2 min")

    # launch background async looping
    asyncio.create_task(auto_loop())


# ----------------------------------------------------------------------
# /stop — stop grid engine
# ----------------------------------------------------------------------
@application.command("stop")
async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.GRID_ACTIVE = False
    await update.message.reply_text("🛑 BOT STOPPED")


# ----------------------------------------------------------------------
# /scan — DEBUG MODE
# Shows:
#   1) RAW bitget futures balance object
#   2) Parsed balance
#   3) Prices of pairs
# ----------------------------------------------------------------------
@application.command("scan")
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # --- Get bitget client ---
    try:
        exchange = bitget_api.get_exchange()
    except Exception as e:
        await update.message.reply_text(f"❌ EXCHANGE INIT ERROR:\n{e}")
        return

    # --- RAW FUTURES BALANCE OBJECT ---
    try:
        raw_balance = exchange.fetch_balance({"type": "swap"})
    except Exception as e:
        await update.message.reply_text(
            f"❌ RAW BALANCE FETCH ERROR:\n{e}")
        return

    # send raw structure (trim for Telegram limit)
    pretty = str(raw_balance)[:3500]
    await update.message.reply_text(
        "📦 RAW BITGET FUTURES BALANCE OBJECT:\n\n" + pretty
    )

    # --- PARSED BALANCE (still zero until we identify keys) ---
    try:
        bal = bitget_api.get_usdt_balance(exchange)
    except Exception as e:
        bal = 0
        print("PARSE ERROR:", e)

    resp = [f"🟡 Parsed Balance = {bal}"]

    # --- Price Debug ---
    for pair in config.PAIRS:
        try:
            price = bitget_api.get_price(exchange, pair)
        except:
            price = 0
        resp.append(f"{pair}: price={price}")

    await update.message.reply_text("\n".join(resp))


# ----------------------------------------------------------------------
# AUTO LOOP — runs every 2 minutes
# ----------------------------------------------------------------------
async def auto_loop():
    await asyncio.sleep(3)

    while True:
        if not config.GRID_ACTIVE:
            await asyncio.sleep(20)
            continue

        try:
            exchange = bitget_api.get_exchange()
            for pair in config.PAIRS:
                # Only DEBUG for now (no trading yet)
                price = bitget_api.get_price(exchange, pair)
                print(f"[AUTO] {pair}: price={price}")
        except Exception as e:
            print("AUTO LOOP ERROR:", e)

        await asyncio.sleep(120)  # 2 min loop


# ----------------------------------------------------------------------
# RUN APP
# ----------------------------------------------------------------------
def main():
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("stop", stop_cmd))
    application.add_handler(CommandHandler("scan", scan))

    print("🤖 Telegram bot is LIVE (Polling mode)")
    application.run_polling(stop_signals=None)


if __name__ == "__main__":
    main()
