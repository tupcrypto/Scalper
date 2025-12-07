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
        f"🤖 GRID AUTO MODE ON\n"
        f"Pairs: {', '.join(config.PAIRS)}\n"
        f"Grid levels: {config.GRID_LEVELS}\n"
        f"Grid range: ±{config.GRID_RANGE_PCT * 100:.2f}% around center\n"
        f"Max capital: {config.MAX_CAPITAL_PCT}%\n"
        f"Live trading: {'ON' if config.LIVE_TRADING else 'OFF'}"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = False
    await update.message.reply_text("🛑 Auto grid mode OFF — no more trades.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = "LIVE (orders placed)" if config.LIVE_TRADING else "SIGNAL ONLY"
    msg = (
        "📊 GRID STATUS\n"
        f"Pairs: {', '.join(config.PAIRS)}\n"
        f"AUTO TRADING: {AUTO_TRADING}\n"
        f"Mode: {mode}\n"
        f"Leverage: {config.LEVERAGE}x\n"
        f"Max capital per pair: {config.MAX_CAPITAL_PCT}%\n"
        f"Grid levels: {config.GRID_LEVELS}\n"
        f"Grid range: ±{config.GRID_RANGE_PCT * 100:.2f}%"
    )
    await update.message.reply_text(msg)


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Manual one-step grid operation
    """
    await update.message.reply_text("🔎 Manual grid scan running...")

    app = context.application
    exchange = bingx_api.get_exchange()
    balance = bingx_api.get_usdt_balance(exchange)

    texts = []

    for pair in config.PAIRS:
        price = bingx_api.get_price(exchange, pair)
        events = grid_engine.step_pair(pair, price, balance)

        if not events:
            texts.append(f"{pair}: No grid actions.")
        else:
            for ev in events:
                if ev["action"] == "reset":
                    texts.append(f"{pair}: 🔄 GRID RESET at {ev['level_price']:.4f}")
                elif ev["action"] == "open":
                    text = f"{pair}: 🟢 OPEN {ev['side']} @ {ev['level_price']:.4f}, TP={ev['tp']:.4f}"
                    texts.append(text)
                    if config.LIVE_TRADING:
                        res = bingx_api.open_position(exchange, pair, ev["side"], ev["amount"])
                        texts.append(res)
                elif ev["action"] == "close":
                    text = f"{pair}: 🔴 CLOSE {ev['side']} from {ev['level_price']:.4f}, TP={ev['tp']:.4f}"
                    texts.append(text)
                    if config.LIVE_TRADING:
                        res = bingx_api.close_position(exchange, pair, ev["side"], ev["amount"])
                        texts.append(res)

    await update.message.reply_text("\n".join(texts))


# =====================================================
# AUTO LOOP  (GRID MODE)
# =====================================================

async def auto_loop(app):
    global AUTO_TRADING
    while True:
        if AUTO_TRADING:
            try:
                exchange = bingx_api.get_exchange()
                balance = bingx_api.get_usdt_balance(exchange)

                for pair in config.PAIRS:
                    price = bingx_api.get_price(exchange, pair)
                    events = grid_engine.step_pair(pair, price, balance)

                    for ev in events:
                        if ev["action"] == "reset":
                            await notify(app, f"{pair}: 🔄 GRID RESET at {ev['level_price']:.4f}")
                        elif ev["action"] == "open":
                            msg = f"{pair}: 🟢 OPEN {ev['side']} @ {ev['level_price']:.4f}, TP={ev['tp']:.4f}"
                            await notify(app, msg)
                            if config.LIVE_TRADING:
                                res = bingx_api.open_position(exchange, pair, ev["side"], ev["amount"])
                                await notify(app, res)
                        elif ev["action"] == "close":
                            msg = f"{pair}: 🔴 CLOSE {ev['side']} from {ev['level_price']:.4f}, TP={ev['tp']:.4f}"
                            await notify(app, msg)
                            if config.LIVE_TRADING:
                                res = bingx_api.close_position(exchange, pair, ev["side"], ev["amount"])
                                await notify(app, res)

            except Exception as e:
                await notify(app, f"❌ AUTO LOOP ERROR: {e}")

        await asyncio.sleep(30)  # faster loop


# =====================================================
# START APP
# =====================================================

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("status", status))

    asyncio.get_event_loop().create_task(auto_loop(app))

    print("BOT STARTED AND POLLING...")
    app.run_polling()


if __name__ == "__main__":
    main()
