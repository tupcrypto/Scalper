import ccxt

def get_exchange(api_key, api_secret, password):
    exchange = ccxt.bitget({
        "apiKey": api_key,
        "secret": api_secret,
        "password": password,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",  # futures mode
        }
    })
    return exchange


def get_grid_action(price, lower, upper):
    if price < lower:
        return "LONG_ENTRY"
    elif price > upper:
        return "SHORT_ENTRY"
    else:
        return "HOLD"


def execute_order(exchange, symbol, signal, balance, leverage=5):
    try:
        if signal not in ["LONG_ENTRY", "SHORT_ENTRY"]:
            return "NO ORDER"

        ticker = exchange.fetch_ticker(symbol)
        price = float(ticker['last'])

        risk_pct = 0.20
        order_cost = balance * risk_pct

        if symbol == "BTC/USDT":
            min_cost = 10
        else:
            min_cost = 6

        if order_cost < min_cost:
            return f"NO ORDER — COST {order_cost:.2f} < MIN {min_cost}"

        qty = order_cost / price

        params = {
            "reduceOnly": False,
            "leverage": leverage,
        }

        if signal == "LONG_ENTRY":
            exchange.create_order(
                symbol=symbol,
                type='market',
                side='buy',
                amount=float(qty),
                params=params
            )
            return f"ORDER OK — LONG {symbol} qty={qty:.6f}"

        if signal == "SHORT_ENTRY":
            exchange.create_order(
                symbol=symbol,
                type='market',
                side='sell',
                amount=float(qty),
                params=params
            )
            return f"ORDER OK — SHORT {symbol} qty={qty:.6f}"

        return "NO ORDER"

    except Exception as e:
        return f"ORDER ERROR: {str(e)}"


def trade_symbol(exchange, symbol, balance, grid_range=0.004):
    ticker = exchange.fetch_ticker(symbol)
    price = float(ticker['last'])

    lower = price * (1 - grid_range)
    upper = price * (1 + grid_range)

    action = get_grid_action(price, lower, upper)
    result = execute_order(exchange, symbol, action, balance)

    return {
        "symbol": symbol,
        "price": price,
        "lower": lower,
        "upper": upper,
        "action": action,
        "result": result
    }
