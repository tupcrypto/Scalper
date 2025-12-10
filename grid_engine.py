import math
import ccxt

# ===============================
# GRID DECISION LOGIC
# ===============================

def get_grid_action(price, lower, upper):
    """
    Decide LONG, SHORT or HOLD based on grid levels.
    """
    if price < lower:
        return "LONG_ENTRY"
    elif price > upper:
        return "SHORT_ENTRY"
    else:
        return "HOLD"


# ===============================
# EXECUTE ORDER ON BITGET FUTURES (MARKET)
# ===============================

def execute_order(exchange, symbol, signal, balance, leverage=5):
    try:
        # No action required
        if signal not in ["LONG_ENTRY", "SHORT_ENTRY"]:
            return "NO ORDER"

        ticker = exchange.fetch_ticker(symbol)
        price = float(ticker['last'])

        # ====================
        # CAPITAL ALLOCATION
        # ====================
        risk_pct = 0.20   # 20% per grid order (adjustable)
        order_cost = balance * risk_pct

        # =============================================
        # BITGET MINIMUM FUTURES ORDER COST ENFORCEMENT
        # =============================================
        # Based on live exchange rules you confirmed:
        # BTC ≈ $9.5    SUI ≈ $5.5
        if symbol == "BTC/USDT":
            min_cost = 10
        else:
            min_cost = 6

        if order_cost < min_cost:
            return f"NO ORDER — COST {order_cost:.2f} < MIN {min_cost}"

        # ===================
        # ORDER QUANTITY
        # ===================
        qty = order_cost / price

        # Bitget parameters
        params = {
            "reduceOnly": False,
            "leverage": leverage,
        }

        # ===================
        # LONG ORDER
        # ===================
        if signal == "LONG_ENTRY":
            order = exchange.create_order(
                symbol=symbol,
                type='market',
                side='buy',
                amount=qty,
                params=params
            )
            return f"ORDER OK — LONG {symbol} qty={qty:.6f}"

        # ===================
        # SHORT ORDER
        # ===================
        if signal == "SHORT_ENTRY":
            order = exchange.create_order(
                symbol=symbol,
                type='market',
                side='sell',
                amount=qty,
                params=params
            )
            return f"ORDER OK — SHORT {symbol} qty={qty:.6f}"

        return "NO ORDER"

    except Exception as e:
        return f"ORDER ERROR: {str(e)}"


# ===============================
# GRID WRAPPER: MANAGE ONE SYMBOL
# ===============================

def trade_symbol(exchange, symbol, balance, grid_range=0.004):
    """
    A simple neutral grid:
    - center price = current price
    - grid above, grid below
    - decide LONG or SHORT
    """

    ticker = exchange.fetch_ticker(symbol)
    price = float(ticker['last'])

    lower = price * (1 - grid_range)
    upper = price * (1 + grid_range)

    action = get_grid_action(price, lower, upper)

    # EXECUTE trade if valid
    result = execute_order(exchange, symbol, action, balance)

    return {
        "symbol": symbol,
        "price": price,
        "lower": lower,
        "upper": upper,
        "action": action,
        "result": result
    }
