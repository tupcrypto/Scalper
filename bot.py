from __future__ import annotations

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import grid_engine

# =====================================================
# GLOBAL STATE
# =====================================================

AUTO_TRADING = False  # will control auto loop
TELEGRAM_CHAT_ID = config.TELEGRAM_CHAT_ID  # must be numeric


# =====================================================
# SIMPLE NOTIFIER (no separate file yet)
# =====================================================

async def notify_signal(app, text: str):
    """
    Send a Telegram message without requiring a Command handler.
    """
    try:
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
    except Exception as e:
        print("NOTIFY ERROR:", e)


# =====================================================
# TELEGRAM COMMANDS
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = True
    await update.message.reply_text(
        f"🤖 Auto Scalper AUTO-SCAN MODE On for {config.PAIR}\n"
        f"Bot will scan every 2 minutes and send scalp signals."
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = False
    await update.message.reply_text(
        "🛑 Auto Scalp Mode Stopped — no more auto scans."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 BOT STATUS\n"
    msg += f"PAIR: {config.PAIR}\n"
    msg += f"AUTO SCAN MODE: {AUTO_TRADING}\n"
    msg += f"SCAN INTERVAL: 2 min\n"
    msg += f"MODE: SIGNAL ONLY (NO REAL TRADES YET)\n"
    await update.message.reply_text(msg)


async def resetgrid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻ Grid reset will be enabled in auto-trade mode.")


# =====================================================
# MANUAL SCAN COMMAND
# =====================================================

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Manual scan: Checking BTC/USDT...")

    try:
        signal = await asyncio.to_thread(grid_engine.get_scalp_signal, config.PAIR)
    except Exception as e:
        await update.message.reply_text(f"❌ SCAN ERROR: {e}")
        return

    if not signal:
        await update.message.reply_text(
            "😐 No scalp setup right now (mid-range, low vol or dead data)."
        )
        return

    await update.message.reply_text(format_signal(signal))


# =====================================================
# SIGNAL FORMATTER
# =====================================================

def format_signal(signal):
    side = signal["side"]
    entry = signal["entry"]
    tp = signal["tp"]
    sl = signal["sl"]
    low = signal["low"]
    high = signal["high"]
    atr = signal["atr"]
    reason = signal["reason"]
    price = signal["price"]

    return (
        f"🎯 AUTO SCALP SIGNAL ({config.PAIR})\n"
        f"Side: {side}\n"
        f"Current Price: {price:.4f}\n"
        f"Entry: {entry:.4f}\n"
        f"TP: {tp:.4f}\n"
        f"SL: {sl:.4f}\n\n"
        f"Range: {low:.4f} — {high:.4f}\n"
        f"ATR (15m): {atr:.4f}\n\n"
        f"Reason: {reason}\n"
        f"⚠️ SIGNAL ONLY — Bot is NOT placing trades yet."
    )


# =====================================================
# AUTO LOOP — SAFE SIGNAL MODE (NO TRADES)
# =====================================================

async def auto_loop(app):
    global AUTO_TRADING

    while True:
        if AUTO_TRADING:
            try:
                signal = await asyncio.to_thread(grid_engine.get_scalp_signal, config.PAIR)
            except Exception as e:
                print("AUTO LOOP SCAN ERROR:", e)
                await notify_signal(app, f"❌ AUTO SCAN ERROR: {e}")
                await asyncio.sleep(120)
                continue

            if signal:
                formatted = format_signal(signal)
                await notify_signal(app, formatted)

        # scan interval
        await asyncio.sleep(120)  # 2 minutes between scans


# =====================================================
# MAIN — RENDER FRIENDLY
# =====================================================

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("resetgrid", resetgrid))
    app.add_handler(CommandHandler("scan", scan))

    # run auto loop in background
    asyncio.get_event_loop().create_task(auto_loop(app))

    print("BOT STARTED AND POLLING...")
    app.run_polling()


if __name__ == "__main__":
    main()
