import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import grid_engine

# =====================================================
# GLOBAL STATE
# =====================================================

AUTO_TRADING = False  # will use later when we add auto mode


# =====================================================
# TELEGRAM COMMANDS
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = True
    await update.message.reply_text(f"🤖 Auto Scalper Started (signal mode) for {config.PAIR}")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = False
    await update.message.reply_text("🛑 Auto Scalper Stopped (no auto signals will be generated)")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 BOT STATUS\n"
    msg += f"PAIR: {config.PAIR}\n"
    msg += f"AUTO TRADING FLAG: {AUTO_TRADING}\n"
    msg += f"LEVERAGE (planned): {config.LEVERAGE}x\n"
    msg += f"MAX CAPITAL USED (planned): {config.MAX_CAPITAL_PCT}%\n"
    msg += "MODE: Signal-only (no real orders yet)\n"
    await update.message.reply_text(msg)


async def resetgrid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻️ Grid reset logic will be added when auto-trading is enabled.")


# -------- NEW: /scan command --------

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Manually trigger a scalping scan on BTC/USDT and return a signal (if any).
    """
    await update.message.reply_text("🔎 Scanning market for BTC/USDT scalp setup...")

    # Run heavy work in a thread so we don't block the bot
    signal = await asyncio.to_thread(grid_engine.get_scalp_signal, config.PAIR)

    if not signal:
        await update.message.reply_text("😐 No high-probability scalp setup right now. Market is either dead or in the middle of the range.")
        return

    side = signal["side"]
    entry = signal["entry"]
    sl = signal["sl"]
    tp = signal["tp"]
    rr = signal["rr"]
    low = signal["range_low"]
    high = signal["range_high"]
    atr = signal["atr"]
    reason = signal["reason"]
    price = signal["price"]

    rr_text = f"{rr:.2f}" if rr is not None else "N/A"

    msg = (
        f"🎯 SCALP SIGNAL ({signal['pair']})\n"
        f"Side: {side}\n"
        f"Current Price: {price:.4f}\n"
        f"Entry (now): {entry:.4f}\n"
        f"TP: {tp:.4f}\n"
        f"SL: {sl:.4f}\n"
        f"Approx R:R: {rr_text}\n\n"
        f"Range Low: {low:.4f}\n"
        f"Range High: {high:.4f}\n"
        f"ATR (15m): {atr:.4f}\n\n"
        f"Reason: {reason}\n"
        f"⚠️ This is SIGNAL-ONLY, bot is NOT placing real orders yet."
    )

    await update.message.reply_text(msg)


# =====================================================
# MAIN — BLOCKING POLLING (Render-friendly)
# =====================================================

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("resetgrid", resetgrid))
    app.add_handler(CommandHandler("scan", scan))  # new command

    print("BOT STARTED AND POLLING...")
    app.run_polling()


if __name__ == "__main__":
    main()

