from __future__ import annotations

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import grid_engine

# =====================================================
# GLOBAL STATE
# =====================================================

AUTO_TRADING = False  # we will use this later for auto mode


# =====================================================
# TELEGRAM COMMANDS
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = True
    await update.message.reply_text(
        f"🤖 Auto Scalper Started (signal mode) for {config.PAIR}"
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = False
    await update.message.reply_text(
        "🛑 Auto Scalper Stopped (no automatic scans for now)."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 BOT STATUS\n"
    msg += f"PAIR: {config.PAIR}\n"
    msg += f"AUTO TRADING FLAG: {AUTO_TRADING}\n"
    msg += f"LEVERAGE (planned): {config.LEVERAGE}x\n"
    msg += f"MAX CAPITAL USED (planned): {config.MAX_CAPITAL_PCT}%\n"
    msg += "MODE: Signal-only (no real orders yet)\n"
    await update.message.reply_text(msg)

async def resetgrid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "♻️ Grid reset logic will be added when auto-trading mode is enabled."
    )


# -----------------------------------------------------
# /scan  — main scalp signal command
# -----------------------------------------------------

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Manually trigger a scalping scan on BTC/USDT and return a signal (if any).
    """
    await update.message.reply_text("🔎 Scanning BTC/USDT for a scalp setup...")

    try:
        # run blocking ccxt/pandas work in a thread so bot stays responsive
        signal = await asyncio.to_thread(grid_engine.get_scalp_signal, config.PAIR)
    except Exception as e:
        # if anything explodes, we SEE it in Telegram
        await update.message.reply_text(f"❌ INTERNAL SCAN ERROR: {e}")
        return

    if not signal:
        await update.message.reply_text(
            "😐 No good scalp setup right now (mid-range, low vol, or bad data)."
        )
        return

    side = signal["side"]
    entry = signal["entry"]
    tp = signal["tp"]
    sl = signal["sl"]
    low = signal["low"]
    high = signal["high"]
    atr = signal["atr"]
    reason = signal["reason"]
    price = signal["price"]

    msg = (
        f"🎯 SCALP SIGNAL ({config.PAIR})\n"
        f"Side: {side}\n"
        f"Current Price: {price:.4f}\n"
        f"Entry (now): {entry:.4f}\n"
        f"TP: {tp:.4f}\n"
        f"SL: {sl:.4f}\n\n"
        f"Range: {low:.4f} — {high:.4f}\n"
        f"ATR (15m): {atr:.4f}\n\n"
        f"Reason: {reason}\n"
        f"⚠️ SIGNAL ONLY — bot is NOT placing real orders yet."
    )

    await update.message.reply_text(msg)


# =====================================================
# MAIN — Render-friendly blocking polling
# =====================================================

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("resetgrid", resetgrid))
    app.add_handler(CommandHandler("scan", scan))

    print("BOT STARTED AND POLLING...")
    app.run_polling()


if __name__ == "__main__":
    main()
