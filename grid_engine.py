import config
import bitget_api
import math

# ============================================================
# BASIC GRID LOGIC (SAFE + SIMPLE)
# ============================================================

# center price logic (keeps grid dynamic)
def get_center(price):
    return price


# grid boundaries (% around price)
def get_bounds(price):
    rng = config.GRID_RANGE_PCT
    upper = price * (1 + rng)
    lower = price * (1 - rng)
    return lower, upper


# ============================================================
# MAIN CHECK FUNCTION — called by /scan and auto_loop
# ============================================================
def check_grid_signal(pair, price, balance):

    # boundaries
    lower, upper = get_bounds(price)

    # decision logic
    if price < lower:
        return "❗ BUY SIGNAL — below grid, mean reversion entry"

    if price > upper:
        return "❗ SELL SIGNAL — above grid, mean reversion entry"

    return "No grid actions"


# ============================================================
# EXECUTION LOGIC (ONLY WHEN LIVE TRADING IS ON)
# ============================================================
def execute_if_needed(pair, price, balance):

    if not config.LIVE_TRADING:
        return

    # get signal
    signal = check_grid_signal(pair, price, balance)

    if "BUY" in signal:
        # position sizing — very basic
        allocation = balance * (config.MAX_CAPITAL_PCT / 100)
        qty = allocation / price

        ex = bitget_api.get_exchange()
        try:
            order = ex.create_order(
                symbol=pair,
                type="market",
                side="buy",
                amount=qty,
            )
            print(f"[LIVE] BUY ORDER SENT for {pair} qty={qty}")
        except Exception as e:
            print(f"[LIVE BUY ERROR]: {str(e)}")

    elif "SELL" in signal:
        allocation = balance * (config.MAX_CAPITAL_PCT / 100)
        qty = allocation / price

        ex = bitget_api.get_exchange()

        try:
            order = ex.create_order(
                symbol=pair,
                type="market",
                side="sell",
                amount=qty,
            )
            print(f"[LIVE] SELL ORDER SENT for {pair} qty={qty}")
        except Exception as e:
            print(f"[LIVE SELL ERROR]: {str(e)}")
