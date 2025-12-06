import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config

# ==============================================================================================
# GLOBAL STATE
# ==============================================================================================

AUTO_TRADING = False   # runtime switch


# ==============================================================================================
# TELEGRAM COMMANDS
# ==============================================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = True
    await update.message.reply_text(f"🤖 Auto Scalper Skeleton Started for {config.PAIR}")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADING
    AUTO_TRADING = False
    await update.message.reply_text("🛑 Auto Scalper Stopped")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 BOT STATUS\n"
    msg += f"PAIR: {config.PAIR}\n"
    msg += f"AUTO TRADING: {AUTO_TRADING}\n"
    msg += f"LEVERAGE: {config.LEVERAGE}x\n"
    msg += f"MAX CAPITAL USED: {config.MAX_CAPITAL_PCT}%\n"
    await update.message.reply_text(msg)


async def resetgrid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻️ Grid Reset — (not implemented yet)")


# ==============================================================================================
# MAIN LOOP — CURRENTLY IDLE (NO SCANNER YET)
# ==============================================================================================

async def run_loop():
    global AUTO_TRADING
    while True:
        # placeholder — doing nothing for now
        await asyncio.sleep(3)


# ==============================================================================================
# BOOTSTRAP TELEGRAM BOT
# ==============================================================================================

async def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("resetgrid", resetgrid))

    asyncio.create_task(run_loop())

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
