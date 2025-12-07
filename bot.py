from __future__ import annotations

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import grid_engine
import bingx_api

AUTO_TRADING = False
TELEGRAM_CHAT_ID = config.TELEGRAM_CHAT_ID


# =====================================================
# NOTIFIER
# =====================================================

async def notify(app, text: str):
    if TELEGRAM_CHAT_ID == 0:
        print("TELEGRAM_CHAT_ID is 0, cannot notify.")
        return
    try:
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
    except Exception as e:
        print("NOTIFY ERROR:", e)


# =====================================================
# COMMANDS
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = True
    await update.message.reply_text(
        f"🤖 Auto Scalper AUTO MODE ON\n"
        f"Pairs: {', '.join(config.PAIRS)}\n"
        f"Scan interval: 2 min\n"
        f"Live trading: {'ON' if config.LIVE_TRADING else 'OFF'}"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = False
    await update.message.reply_text("🛑 Auto mode OFF — no more auto scans/trades.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 BOT STATUS\n"
    msg += f"Pairs: {', '.join(config.PAIRS)}\n"
    msg += f"AUTO MODE: {AUTO_TRADING}\n"
    msg += f"SCAN INTERVAL: 2 min\n"
    msg += f"MODE: {'LIVE' if config.LIVE_TRADING else 'SIGNAL-ONLY'}\n"
    msg += f"LEVERAGE: {config.LEVERAGE}x\n"
    msg += f"MAX CAPITAL PER TRADE: {config.MAX_CAPITAL_PCT}%\n"
    await update.message.reply_text(msg)


async def resetgrid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻ Grid is recalculated every scan (no static grid to reset).")


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Manual scan on all pairs...")

    texts = []
    for pair in config.PAIRS:
        try:
            signal = await asyncio.to_thread(grid_engine.get_scalp_signal, pair)
        except Exception as e:
            texts.append(f"{pair}: ❌ SCAN ERROR: {e}")
            continue

        if not signal:
            texts.append(f"{pair}: 😐 No scalp setup now.")
        else:
            formatted = format_signal(signal)
            texts.append(formatted)

            if config.LIVE_TRADING:
                trade_result = await asyncio.to_thread(bingx_api.execute_trade_from_signal, signal)
                texts.append(trade_result["message"])

    await update.message.reply_text("\n\n".join(texts))


# =====================================================
# SIGNAL FORMATTER
# =====================================================

def format_signal(signal: dict) -> str:
    pair = signal["pair"]
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
        f"🎯 SCALP SIGNAL ({pair})\n"
        f"Side: {side}\n"
        f"Current Price: {price:.4f}\n"
        f"Entry: {entry:.4f}\n"
        f"TP: {tp:.4f}\n"
        f"SL: {sl:.4f}\n"
        f"Range: {low:.4f} — {high:.4f}\n"
        f"ATR (5m): {atr:.4f}\n"
        f"Reason: {reason}\n"
        f"Mode: {'LIVE (orders sent)' if config.LIVE_TRADING else 'SIGNAL ONLY'}"
    )


# =====================================================
# AUTO LOOP
# =====================================================

async def auto_loop(app):
    global AUTO_TRADING
    while True:
        if AUTO_TRADING:
            for pair in config.PAIRS:
                try:
                    signal = await asyncio.to_thread(grid_engine.get_scalp_signal, pair)
                except Exception as e:
                    print(f"AUTO SCAN ERROR for {pair}:", e)
                    await notify(app, f"{pair}: ❌ AUTO SCAN ERROR: {e}")
                    continue

                if signal:
                    formatted = format_signal(signal)
                    await notify(app, formatted)

                    if config.LIVE_TRADING:
                        trade_result = await asyncio.to_thread(
                            bingx_api.execute_trade_from_signal, signal
                        )
                        await notify(app, trade_result["message"])

        await asyncio.sleep(120)  # 2 minutes


# =====================================================
# MAIN
# =====================================================

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("resetgrid", resetgrid))
    app.add_handler(CommandHandler("scan", scan))

    asyncio.get_event_loop().create_task(auto_loop(app))

    print("BOT STARTED AND POLLING...")
    app.run_polling()


if __name__ == "__main__":
    main()
