import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN
from mexc import get_price, get_futures_symbols
from analyzer import analyze_sync

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI Futures Signal Bot is LIVE\n"
        "⏱ TF: 15m + 1h\n"
        "📊 Source: MEXC Futures\n"
        "🧠 AI: OpenRouter"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /scan BTCUSDT")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text("🔍 Analyzing...")

    price = await asyncio.to_thread(get_price, symbol)
    if not price:
        await update.message.reply_text(f"❌ Price unavailable for {symbol}")
        return

    result = await asyncio.to_thread(analyze_sync, symbol, price)
    await update.message.reply_text(result)

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Scanning high-volume futures...")

    symbols = await asyncio.to_thread(get_futures_symbols)
    results = []

    for s in symbols:
        price = await asyncio.to_thread(get_price, s)
        if not price:
            continue

        analysis = await asyncio.to_thread(analyze_sync, s, price)
        if "Probability" in analysis:
            results.append(f"🪙 {s}\n{analysis}")

        if len(results) == 3:
            break

    if not results:
        await update.message.reply_text("❌ NO HIGH-PROBABILITY TRADES FOUND")
    else:
        await update.message.reply_text("\n\n".join(results))

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan", scan))
app.add_handler(CommandHandler("find", find))

app.run_polling()

