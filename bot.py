import os
import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_sync
from config import TELEGRAM_BOT_TOKEN

MEXC_FUTURES_URL = "https://contract.mexc.com/api/v1/contract/ticker"

# ===============================
# MARKET HELPERS
# ===============================

def fetch_markets():
    r = requests.get(MEXC_FUTURES_URL, timeout=10)
    r.raise_for_status()
    return r.json()["data"]


def resolve_symbol(user_symbol: str):
    """
    Convert user input like SUIUSDT / ASTERUSDT
    into real MEXC futures symbol like SUI_USDT
    """
    user_symbol = user_symbol.upper().replace("/", "").replace("-", "")
    markets = fetch_markets()

    for m in markets:
        exch_symbol = m["symbol"].replace("_", "")
        if user_symbol == exch_symbol:
            return m["symbol"]

    # fallback: partial match
    for m in markets:
        if user_symbol.startswith(m["symbol"].split("_")[0]):
            return m["symbol"]

    return None


def get_price(exchange_symbol: str):
    markets = fetch_markets()
    for m in markets:
        if m["symbol"] == exchange_symbol:
            return float(m["lastPrice"])
    return None


def get_top_futures():
    markets = fetch_markets()
    pairs = []

    for m in markets:
        try:
            vol = float(m["volume24"])
            if vol >= 40_000_000:
                pairs.append((m["symbol"], vol))
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
        "/scan SUIUSDT\n"
        "/find"
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /scan SUIUSDT")
        return

    user_symbol = context.args[0]
    msg = await update.message.reply_text("🔍 Resolving symbol...")

    exchange_symbol = await asyncio.to_thread(resolve_symbol, user_symbol)
    if not exchange_symbol:
        await msg.edit_text(f"❌ Futures pair not found for {user_symbol}")
        return

    price = await asyncio.to_thread(get_price, exchange_symbol)
    if not price:
        await msg.edit_text(f"❌ Price unavailable for {exchange_symbol}")
        return

    await msg.edit_text("🧠 AI analyzing market structure...")

    result = await asyncio.to_thread(
        analyze_sync, exchange_symbol, price
    )

    await msg.edit_text(
        f"📊 {exchange_symbol}\n"
        f"💰 Price: {price}\n\n"
        f"{result}"
    )


async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Scanning high-volume MEXC futures...")

    symbols = await asyncio.to_thread(get_top_futures)

    for sym in symbols:
        price = await asyncio.to_thread(get_price, sym)
        if not price:
            continue

        analysis = await asyncio.to_thread(analyze_sync, sym, price)

        await update.message.reply_text(
            f"📊 {sym}\n"
            f"💰 Price: {price}\n\n"
            f"{analysis}"
        )

        await asyncio.sleep(1.5)  # OpenRouter rate safety


# ===============================
# MAIN
# ===============================

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("find", find))

    print("🤖 Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()

