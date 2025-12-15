from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN, MIN_PROBABILITY
from mexc import get_futures_symbols, get_price
from analyzer import analyze

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
    price = get_price(symbol)
    result = analyze(symbol, price)
    await update.message.reply_text(result)

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbols = get_futures_symbols()
    replies = []

    for s in symbols:
        price = get_price(s)
        analysis = analyze(s, price)
        if "Probability" in analysis:
            replies.append(f"🔍 {s}\n{analysis}")
        if len(replies) == 3:
            break

    if not replies:
        await update.message.reply_text("❌ NO HIGH-PROBABILITY TRADES FOUND")
    else:
        await update.message.reply_text("\n\n".join(replies))

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan", scan))
app.add_handler(CommandHandler("find", find))

app.run_polling()

