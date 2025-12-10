import ccxt.async_support as ccxt
import config


def get_exchange():
    return ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",
        }
    })


async def get_balance(exchange):
    try:
        balance = await exchange.fetch_balance()
        return float(balance["total"]["USDT"])
    except:
        return 0.0


async def trade_symbol(exchange, symbol, balance):
    try:
        ticker = await exchange.fetch_ticker(symbol)
        price = float(ticker["last"])

        if balance < config.MIN_ORDER[symbol]:
            return {
                "action": "NO ORDER",
                "price": price,
                "result": f"Balance {balance} too small",
            }

        cost = config.MIN_ORDER[symbol]
        amount = cost / price

        order = await exchange.create_order(
            symbol=symbol,
            type="market",
            side="buy",
            amount=amount,
        )

        return {
            "action": "LONG",
            "price": price,
            "result": f"ORDER OK: cost={cost}, amount={amount}"
        }

    except Exception as e:
        return {
            "action": "ERROR",
            "price": 0,
            "result": str(e),
        }
