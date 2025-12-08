from __future__ import annotations

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import grid_engine
import bingx_api

# =====================================================
# GLOBAL STATE
# =====================================================

AUTO_TRADING = False
TELEGRAM_CHAT_ID = config.TELEGRAM_CHAT_ID


# =====================================================
# NOTIFIER
# =====================================================

async def notify(app, text: str):
    """Send a message to your main chat ID (no crash if 0)."""
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
        f"Max capital per pair: {config.MAX_CAPITAL_PCT}%\n"
        f"Leverage: {config.LEVERAGE}x\n"
        f"Live trading: {'ON' if config.LIVE_TRADING else 'OFF'}"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = False
    await update.message.reply_text("🛑 Auto grid mode OFF — no more auto trades.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = "LIVE (orders sent)" if config.LIVE_TRADING else "SIGNAL ONLY (no orders)"
    msg = (
        "📊 GRID BOT STATUS\n"
        f"Pairs: {', '.join(config.PAIRS)}\n"
        f"AUTO MODE: {AUTO_TRADING}\n"
        f"Mode: {mode}\n"
        f"Leverage: {config.LEVERAGE}x\n"
        f"Max capital per pair: {config.MAX_CAPITAL_PCT}%\n"
        f"Grid levels: {config.GRID_LEVELS}\n"
        f"Grid range: ±{config.GRID_RANGE_PCT * 100:.2f}% around center"
    )
    await update.message.reply_text(msg)


async def resetgrid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Actual reset is automatic on breakout; here we just explain.
    await update.message.reply_text(
        "♻ Grid is automatically re-centered on breakout.\n"
        "To force a reset: /stop then /start."
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Manual one-step grid operation (debug-friendly).
    Shows price & balance and executes grid events once.
    """
    await update.message.reply_text("🔎 Running ONE manual grid step on all pairs...")

    app = context.application

    # 1) Try to create exchange (this is where ccxt/bingx can fail)
    try:
        exchange = bingx_api.get_exchange()
    except Exception as e:
        err = f"❌ EXCHANGE ERROR (get_exchange): {e}"
        print(err)
        await update.message.reply_text(err)
        return

    # 2) Fetch balance once
    balance = bingx_api.get_usdt_balance(exchange)
    print("SCAN DEBUG — BALANCE USDT:", balance)

    texts = [f"SCAN DEBUG — BALANCE USDT: {balance}"]

    for pair in config.PAIRS:
        price = bingx_api.get_price(exchange, pair)
        print(f"SCAN DEBUG — {pair} PRICE:", price)

        texts.append(f"{pair}: price={price}")

        events = grid_engine.step_pair(pair, price, balance)

        if not events:
            texts.append(f"{pair}: No grid actions this step.")
        else:
            for ev in events:
                if ev["action"] == "reset":
                    txt = f"{pair}: 🔄 GRID RESET around {ev['level_price']:.4f}"
                    texts.append(txt)
                elif ev["action"] == "open":
                    txt = (
                        f"{pair}: 🟢 OPEN {ev['side']} @ {ev['level_price']:.4f}, "
                        f"TP={ev['tp']:.4f}, amount={ev['amount']}"
                    )
                    texts.append(txt)
                    if config.LIVE_TRADING:
                        res = bingx_api.open_position(exchange, pair, ev["side"], ev["amount"])
                        texts.append(res)
                elif ev["action"] == "close":
                    txt = (
                        f"{pair}: 🔴 CLOSE {ev['side']} from {ev['level_price']:.4f}, "
                        f"TP={ev['tp']:.4f}, amount={ev['amount']}"
                    )
                    texts.append(txt)
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
                # 1) Exchange + balance
                exchange = bingx_api.get_exchange()
                balance = bingx_api.get_usdt_balance(exchange)
                print("AUTO DEBUG — BALANCE USDT:", balance)

                for pair in config.PAIRS:
                    price = bingx_api.get_price(exchange, pair)
                    print(f"AUTO DEBUG — {pair} PRICE:", price)

                    events = grid_engine.step_pair(pair, price, balance)

                    for ev in events:
                        if ev["action"] == "reset":
                            msg = f"{pair}: 🔄 GRID RESET around {ev['level_price']:.4f}"
                            await notify(app, msg)

                        elif ev["action"] == "open":
                            msg = (
                                f"{pair}: 🟢 OPEN {ev['side']} @ {ev['level_price']:.4f}, "
                                f"TP={ev['tp']:.4f}, amount={ev['amount']}"
                            )
                            await notify(app, msg)
                            if config.LIVE_TRADING:
                                res = bingx_api.open_position(exchange, pair, ev["side"], ev["amount"])
                                await notify(app, res)

                        elif ev["action"] == "close":
                            msg = (
                                f"{pair}: 🔴 CLOSE {ev['side']} from {ev['level_price']:.4f}, "
                                f"TP={ev['tp']:.4f}, amount={ev['amount']}"
                            )
                            await notify(app, msg)
                            if config.LIVE_TRADING:
                                res = bingx_api.close_position(exchange, pair, ev["side"], ev["amount"])
                                await notify(app, res)

            except Exception as e:
                err = f"❌ AUTO LOOP ERROR: {e}"
                print(err)
                await notify(app, err)

        # grid needs more frequent checks than scalping – 30s is okay
        await asyncio.sleep(30)


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

    # launch grid auto loop in background
    asyncio.get_event_loop().create_task(auto_loop(app))

    print("BOT STARTED AND POLLING...")
    app.run_polling()


if __name__ == "__main__":
    main()
