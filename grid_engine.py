import ccxt.async_support as ccxt
import config
import logging

logger = logging.getLogger(__name__)

# Create exchange instance
exchange = ccxt.blofin({
    "apiKey": config.API_KEY,
    "secret": config.API_SECRET,
    "password": config.API_PASSWORD,
    "enableRateLimit": True,
})


# ------------------------------------------------
# Get balance
# ------------------------------------------------
async def get_balance():
    try:
        balances = await exchange.fetch_balance()
        total = balances.get("total", {})
        return float(total.get("USDT", 0))
    except Exception as e:
        logger.error(f"BALANCE ERROR: {e}")
        return 0


# ------------------------------------------------
# Get price
# ------------------------------------------------
async def get_price(symbol):
    try:
        ticker = await exchange.fetch_ticker(symbol)
        return ticker["last"]
    except Exception as e:
        logger.error(f"PRICE ERROR {symbol}: {e}")
        return None


# ------------------------------------------------
# Place GRID trades
# ------------------------------------------------
async def run_grid(symbol, price):
    balance = await get_balance()

    if balance < config.ORDER_SIZE_USDT:
        logger.info(f"[GRID] {symbol} — NO ORDER, balance too low ({balance})")
        return

    try:
        # Example: simple neutral grid – BUY below price, SELL above price
        buy_price = price * 0.997
        sell_price = price * 1.003
        amount = config.ORDER_SIZE_USDT / price

        # BUY LIMIT
        await exchange.create_order(
            symbol=symbol,
            type="limit",
            side="buy",
            price=round(buy_price, 2),
            amount=round(amount, 3)
        )

        # SELL LIMIT
        await exchange.create_order(
            symbol=symbol,
            type="limit",
            side="sell",
            price=round(sell_price, 2),
            amount=round(amount, 3)
        )

        logger.info(f"[GRID] {symbol} — Orders placed")

    except Exception as e:
        logger.error(f"GRID ORDER ERROR {symbol}: {e}")


# ------------------------------------------------
# Get full market list
# ------------------------------------------------
async def get_markets():
    try:
        markets = await exchange.load_markets()
        return list(markets.keys())
    except Exception as e:
        logger.error(f"MARKETS ERROR: {e}")
        return []

