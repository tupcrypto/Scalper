import os
import asyncio
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from analyzer import analyze_sync
from config import TELEGRAM_BOT_TOKEN

MEXC_FUTURES_URL = "https://contract.mexc.com/api/v1/contract/ticker"

# ===============================
# UTILITIES
# ===============================

def get_price(symbol: str):
    try:
        r = requests.get(MEXC_FUTURES_URL, timeout=10)
        data = r.json()["data"]
        for item in data:
            if item["symbol"] == symbol:
                return float(item["lastPrice"])
    except:
        pass
    return None


def get_top_futures():
    r = requests.get(MEXC_FUTURES_URL, timeout=10)
    data = r.json()["data"]

    pairs = []
    for item in data:
        try:
            vol = float(item["volume24"])
            if vol >= 40_000_000:
                pairs.append((item["symbol"], vol))
        except:
            continue

    pairs.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in pairs[:3]]


# ===============================
# COMMANDS
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI Futures Signal Bot is LIVE\n"
        "⏱ Timeframes: 15m + 1h\n"
        "📊 Exchange: MEXC Futures\n"
        "🧠 AI: OpenRouter\n\n"
        "Commands:\n"
        "/scan BTCUSDT\n"
        "/find"
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /scan BTCUSDT")
        return

    symbol = context.args[0].upper()
    msg = await update.message.reply_text("🔍 Analyzing (AI thinking)...")

    price = await asyncio.to_thread(get_price, symbol)
    if not price:
        await msg.edit_text(f"❌ Price unavailable for {symbol}")
        return

    result = await asyncio.to_thread(analyze_sync, symbol, price)
    await msg.edit_text(result)


async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Scanning high-volume MEXC futures...")

    symbols = await asyncio.to_thread(get_top_futures)

    if not symbols:
        await update.message.reply_text("❌ No high-volume pairs found.")
        return

    for sym in symbols:
        price = await asyncio.to_thread(get_price, sym)
        if not price:
            continue

        analysis = await asyncio.to_thread(analyze_sync, sym, price)
        await update.message.reply_text(f"📊 {sym}\n{analysis}")

        # rate-limit OpenRouter
        await asyncio.sleep(1.5)


# ===============================
# MAIN
# ===============================

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("find", find))

    print("🤖 Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()

