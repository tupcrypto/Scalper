import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import config
import grid_engine
import bitget_api

# --------------------------------------------------------------
# GET BALANCE (ASSUMED MODE ONLY — NO BITGET API CALLS)
# --------------------------------------------------------------
def get_bot_balance():
    # ALWAYS return assumed balance
    return config.ASSUMED_BALANCE_USDT


# --------------------------------------------------------------
# /scan — get prices and grid decisions
# --------------------------------------------------------------
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = get_bot_balance()

    msg = f"SCAN DEBUG — BALANCE: {balance} USDT\n"
    for p in config.PAIRS:
        try:
            price = bitget_api.get_price(p)
            msg += f"{p}: price={price}\n"
            decision = grid_engine.check_grid_signal(p, price, balance)
            msg += f"{p}: {decision}\n"
        except Exception as e:
            msg += f"{p}: SCAN ERROR: {str(e)}\n"

    await update.message.reply_text(msg)


# --------------------------------------------------------------
# /start — begin auto loop
# --------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_task
    if config.GRID_ACTIVE:
        await update.message.reply_text("Bot already running!")
        return

    config.GRID_ACTIVE = True
    await update.message.reply_text("BOT STARTED AND POLLING...")

    auto_task = asyncio.create_task(auto_loop())


# --------------------------------------------------------------
# /stop — stop loop
# --------------------------------------------------------------
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_task
    config.GRID_ACTIVE = False
    try:
        auto_task.cancel()
    except:
        pass

    await update.message.reply_text("BOT STOPPED.")


# --------------------------------------------------------------
# AUTO LOOP — DOES NOT READ BALANCE FROM API
# --------------------------------------------------------------
async def auto_loop():
    while config.GRID_ACTIVE:
        try:
            balance = get_bot_balance()
            for p in config.PAIRS:
                price = bitget_api.get_price(p)
                decision = grid_engine.check_grid_signal(p, price, balance)

                # send logs to Telegram if needed
                print(f"[AUTO] {p}: {decision}")

                # LIVE orders execute inside grid_engine
                if config.LIVE_TRADING:
                    grid_engine.execute_if_needed(p, price, balance)

        except Exception as e:
            print(f"AUTO LOOP ERROR: {str(e)}")

        await asyncio.sleep(120)


# --------------------------------------------------------------
# BOOTSTRAP TELEGRAM
# --------------------------------------------------------------
application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(CommandHandler("scan", scan))


if __name__ == "__main__":
    application.run_polling()
