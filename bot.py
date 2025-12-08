from __future__ import annotations

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import grid_engine
import bitget_api

AUTO_TRADING = False
TELEGRAM_CHAT_ID = config.TELEGRAM_CHAT_ID


# =====================================================
# SEND MESSAGE
# =====================================================

async def notify(app, text: str):
    if not TELEGRAM_CHAT_ID:
        print(text)
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
        f"🤖 BITGET GRID AUTO MODE ON\n"
        f"Pairs: {', '.join(config.PAIRS)}\n"
        f"Grid Levels: {config.GRID_LEVELS}\n"
        f"Grid Range: ±{config.GRID_RANGE_PCT*100:.2f}%\n"
        f"Capital: {config.MAX_CAPITAL_PCT}%\n"
        f"Live mode: {config.LIVE_TRADING}"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = False
    await update.message.reply_text("🛑 Auto grid OFF")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = "LIVE" if config.LIVE_TRADING else "SIGNAL ONLY"
    msg = (
        f"📊 STATUS\n"
        f"Auto trading: {AUTO_TRADING}\n"
        f"Mode: {mode}\n"
        f"Leverage: {config.LEVERAGE}\n"
        f"Capital: {config.MAX_CAPITAL_PCT}%\n"
        f"Pairs: {', '.join(config.PAIRS)}"
    )
    await update.message.reply_text(msg)


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual debug step"""
    app = context.application

    try:
        exchange = bitget_api.get_exchange()
    except Exception as e:
        await update.message.reply_text(f"❌ EXCHANGE ERROR: {e}")
        return

    balance = bitget_api.get_usdt_balance(exchange)
    texts = [f"SCAN DEBUG — BALANCE: {balance}"]

    for pair in config.PAIRS:
        price = bitget_api.get_price(exchange, pair)
        texts.append(f"{pair}: price={price}")

        events = grid_engine.step_pair(pair, price, balance)

        if not events:
            texts.append(f"{pair}: No grid actions")
        else:
            for ev in events:
                if ev["action"] == "open":
                    txt = f"{pair}: 🟢 OPEN {ev['side']} @ {ev['level_price']} TP={ev['tp']}"
                    texts.append(txt)
                    if config.LIVE_TRADING:
                        res = bitget_api.open_position(exchange, pair, ev["side"], ev["amount"])
                        texts.append(res)

                elif ev["action"] == "close":
                    txt = f"{pair}: 🔴 CLOSE {ev['side']} from {ev['level_price']} TP HIT"
                    texts.append(txt)
                    if config.LIVE_TRADING:
                        res = bitget_api.close_position(exchange, pair, ev["side"], ev["amount"])
                        texts.append(res)

    await update.message.reply_text("\n".join(texts))


# =====================================================
# AUTO LOOP
# =====================================================

async def auto_loop(app):
    global AUTO_TRADING

    while True:
        if AUTO_TRADING:
            try:
                exchange = bitget_api.get_exchange()
                balance  = bitget_api.get_usdt_balance(exchange)

                for pair in config.PAIRS:
                    price = bitget_api.get_price(exchange, pair)
                    events = grid_engine.step_pair(pair, price, balance)

                    for ev in events:
                        if ev["action"] == "open":
                            msg = f"{pair}: 🟢 OPEN {ev['side']} @ {ev['level_price']} TP={ev['tp']}"
                            await notify(app, msg)
                            if config.LIVE_TRADING:
                                res = bitget_api.open_position(exchange, pair, ev["side"], ev["amount"])
                                await notify(app, res)

                        elif ev["action"] == "close":
                            msg = f"{pair}: 🔴 CLOSE {ev['side']} TP HIT"
                            await notify(app, msg)
                            if config.LIVE_TRADING:
                                res = bitget_api.close_position(exchange, pair, ev["side"], ev["amount"])
                                await notify(app, res)

            except Exception as e:
                await notify(app, f"❌ AUTO ERROR: {e}")

        await asyncio.sleep(30)  # frequency


# =====================================================
# MAIN
# =====================================================

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("scan", scan))

    asyncio.get_event_loop().create_task(auto_loop(app))

    print("BOT STARTED")
    app.run_polling()


if __name__ == "__main__":
    main()

