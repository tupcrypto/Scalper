import ccxt.async_support as ccxt
import math
import config

# ------------------------------------------------
# CREATE FUTURES EXCHANGE OBJECT
# ------------------------------------------------
async def get_exchange():
    exchange = ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_SECRET_KEY,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",  # FUTURES
            "adjustForTimeDifference": True,
        }
    })
    return exchange

# ------------------------------------------------
# GET REAL BITGET FUTURES BALANCE (CRUCIAL FIX)
# ------------------------------------------------
async def get_balance(exchange):
    try:
        balance = await exchange.fetch_balance()

        # MAIN FUTURES BALANCE LOCATION — MOST ACCURATE FOR BITGET
        usdt = (
            balance.get("info", {})
                   .get("USDT", {})
                   .get("available", None)
        )

        # fallback for other balance responses
        if usdt is None:
            usdt = balance.get("USDT", {}).get("free", 0.0)

        return float(usdt)

    except Exception as e:
        print("BALANCE ERROR:", str(e))
        return 0.0

# ------------------------------------------------
# FETCH CURRENT PRICE
# ------------------------------------------------
async def get_price(exchange, symbol):
    ticker = await exchange.fetch_ticker(symbol)
    return float(ticker["last"])

# ------------------------------------------------
# EXECUTE ORDER (MARKET ORDER)
# ------------------------------------------------
async def execute_order(exchange, symbol, side, amount):
    try:
        # Bitget requires amount as COST for market buys
        # So if side is buy -> cost = amount
        # If side is sell -> amount remains amount (contract size)

        if side.lower() == "buy":
            order = await exchange.create_order(
                symbol=symbol,
                type="market",
                side="buy",
                amount=amount,  # COST IN USDT
                params={"reduceOnly": False}
            )
        else:
            order = await exchange.create_order(
                symbol=symbol,
                type="market",
                side="sell",
                amount=amount,  # COST IN USDT
                params={"reduceOnly": False}
            )

        return order

    except Exception as e:
        print("ORDER ERROR:", str(e))
        return None

# ------------------------------------------------
# GRID DECISION LOGIC
# ------------------------------------------------
async def grid_decision(exchange, symbol, balance):
    price = await get_price(exchange, symbol)

    # If no balance
    if balance < 5:
        return "NO_ORDER", price

    # Pionex-style grid logic (simple demo)
    # Very basic — expand later into advanced grid

    if price % 2 == 0:  # random condition
        return "LONG", price
    elif price % 3 == 0:
        return "SHORT", price
    else:
        return "HOLD", price

# ------------------------------------------------
# GRID LOOP
# ------------------------------------------------
async def grid_loop(update, context):
    try:
        exchange = await get_exchange()

        balance = await get_balance(exchange)

        # ------------------
        # BTC
        # ------------------
        action_btc, price_btc = await grid_decision(exchange, "BTC/USDT:USDT", balance)

        if action_btc == "LONG":
            cost = max(5.5, balance * 0.03)
            await execute_order(exchange, "BTC/USDT:USDT", "buy", cost)
            await update.message.reply_text(f"[GRID] BTC LONG @ {price_btc}")

        elif action_btc == "SHORT":
            cost = max(5.5, balance * 0.03)
            await execute_order(exchange, "BTC/USDT:USDT", "sell", cost)
            await update.message.reply_text(f"[GRID] BTC SHORT @ {price_btc}")

        else:
            await update.message.reply_text(f"[GRID] BTC — HOLD @ {price_btc}, Balance {balance}")

        # ------------------
        # SUI
        # ------------------
        action_sui, price_sui = await grid_decision(exchange, "SUI/USDT:USDT", balance)

        if action_sui == "LONG":
            cost = max(5.5, balance * 0.03)
            await execute_order(exchange, "SUI/USDT:USDT", "buy", cost)
            await update.message.reply_text(f"[GRID] SUI LONG @ {price_sui}")

        elif action_sui == "SHORT":
            cost = max(5.5, balance * 0.03)
            await execute_order(exchange, "SUI/USDT:USDT", "sell", cost)
            await update.message.reply_text(f"[GRID] SUI SHORT @ {price_sui}")

        else:
            await update.message.reply_text(f"[GRID] SUI — HOLD @ {price_sui}, Balance {balance}")

    except Exception as e:
        await update.message.reply_text(f"[GRID LOOP ERROR] {str(e)}")

