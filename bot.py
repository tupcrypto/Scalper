import asyncio
import config
import bitget_api

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.GRID_ACTIVE = True
    await update.message.reply_text("🚀 BOT STARTED — Auto scan loop ON")
    asyncio.create_task(auto_loop())


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.GRID_ACTIVE = False
    await update.message.reply_text("🛑 BOT STOPPED")


async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        exchange = bitget_api.get_exchange()
    except Exception as e:
        await update.message.reply_text(f"❌ EXCHANGE INIT ERROR:\n{e}")
        return

    # FETCH RAW BALANCE (the correct way)
    try:
        raw_balance = exchange.fetch_balance({"productType": "USDT-FUTURES"})
    except Exception as e:
        await update.message.reply_text(
            f"❌ RAW BALANCE ERROR:\n{e}"
        )
        return

    # SEND RAW DICTIONARY (trimmed)
    pretty = str(raw_balance)[:3500]
    await update.message.reply_text(
        "📦 RAW BITGET FUTURES BALANCE OBJECT:\n\n" + pretty
    )

    # TEMP BALANCE PARSER — will become correct after raw inspection
    try:
        bal = bitget_api.get_usdt_balance(exchange)
    except:
        bal = 0

    lines = [f"🟡 Parsed Balance = {bal}"]

    for pair in config.PAIRS:
        try:
            price = bitget_api.get_price(exchange, pair)
        except:
            price = 0
        lines.append(f"{pair}: price={price}")

    await update.message.reply_text("\n".join(lines))


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

        await asyncio.sleep(120)  # every 2 min


def main():
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("stop", stop_cmd))
    application.add_handler(CommandHandler("scan", scan_cmd))

    print("🤖 Telegram bot LIVE (polling)")
    application.run_polling(stop_signals=None)


if __name__ == "__main__":
    main()
