import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import ccxt
import config
import grid_engine

# -----------------------------------------------------
# GET BITGET EXCHANGE WITH FUTURES BALANCE
# -----------------------------------------------------
def get_exchange():
    exchange = ccxt.bitget({
        'apiKey': config.EXCHANGE_API_KEY,
        'secret': config.EXCHANGE_API_SECRET,
        'password': config.EXCHANGE_PASSPHRASE,
        'options': {
            'defaultType': 'swap',         # <--- Very Important
        }
    })
    exchange.load_markets()
    return exchange

# -----------------------------------------------------
# /scan COMMAND HANDLER
# -----------------------------------------------------
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        exchange = get_exchange()
        balance_raw = exchange.fetch_balance({'type': 'swap'})
        usdt = balance_raw['total']['USDT']
    except Exception as e:
        await update.message.reply_text(f"❌ RAW BALANCE ERROR:\n{e}")
        return

    reply_text = f"SCAN DEBUG — BALANCE: {usdt:.1f} USDT\n"

    for pair in config.PAIRS:
        try:
            ticker = exchange.fetch_ticker(pair)
            price = ticker['last']
            reply_text += f"{pair}: price={price}\n"
            action = grid_engine.check_grid_signal(pair, price, usdt)
            reply_text += f"{pair}: {action}\n"
        except Exception as e:
            reply_text += f"{pair}: SCAN ERROR: {e}\n"

    await update.message.reply_text(reply_text)

# -----------------------------------------------------
# /start AUTO LOOP
# -----------------------------------------------------
AUTO_LOOP_TASK = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_LOOP_TASK

    if AUTO_LOOP_TASK is not None:
        await update.message.reply_text("⚠️ Auto-grid loop already running…")
        return

    await update.message.reply_text("🚀 BOT STARTED AND AUTO-GRID LOOP ACTIVATED…")

    # create task inside loop
    loop = asyncio.get_running_loop()
    AUTO_LOOP_TASK = loop.create_task(auto_loop(context))

# -----------------------------------------------------
# BACKGROUND LOOP
# -----------------------------------------------------
async def auto_loop(context):
    await asyncio.sleep(2)
    print("🔁 AUTO LOOP STARTED")

    while True:
        try:
            exchange = get_exchange()
            balance_raw = exchange.fetch_balance({'type': 'swap'})
            usdt = balance_raw['total']['USDT']
        except Exception as e:
            print(f"[AUTO] BALANCE ERROR: {e}")
            await asyncio.sleep(120)
            continue

        print(f"[AUTO] BALANCE = {usdt}")

        for pair in config.PAIRS:
            try:
                ticker = exchange.fetch_ticker(pair)
                price = ticker['last']
                print(f"[AUTO] {pair} price={price}")

                action = grid_engine.check_grid_signal(pair, price, usdt)
                print(f"[AUTO] {pair} => {action}")

                # ACTUAL TRADE EXECUTIONS
                if config.LIVE_TRADING and action.startswith("BUY"):
                    size = grid_engine.calc_order_size(usdt)
                    order = exchange.create_market_buy_order(pair, size)
                    print(f"[LIVE BUY] {pair} size={size}")

                elif config.LIVE_TRADING and action.startswith("SELL"):
                    size = grid_engine.calc_order_size(usdt)
                    order = exchange.create_market_sell_order(pair, size)
                    print(f"[LIVE SELL] {pair} size={size}")

            except Exception as e:
                print(f"[AUTO] {pair} ERROR: {e}")

        # wait 2 min
        await asyncio.sleep(120)

# -----------------------------------------------------
# BUILD AND RUN BOT
# -----------------------------------------------------
async def post_init(application: Application):
    # START AUTO_LOOP ONLY AFTER BOT IS READY
    global AUTO_LOOP_TASK
    loop = asyncio.get_running_loop()
    AUTO_LOOP_TASK = loop.create_task(auto_loop(None))
    print("🔥 AUTO-LOOP TASK CREATED AFTER INIT")

def main():
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("scan", scan))
    application.add_handler(CommandHandler("start", start))

    application.run_polling()

if __name__ == "__main__":
    main()
