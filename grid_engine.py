import asyncio
import ccxt
import config


# =====================================================
# INIT EXCHANGE CONNECTION FOR BITGET FUTURES
# =====================================================
def get_exchange():
    ex = ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",         # 🚀 FORCE FUTURES MODE
        }
    })
    return ex


# =====================================================
# FETCH FUTURES BALANCE (USDT Perpetual)
# =====================================================
async def get_balance(exchange) -> float:
    try:
        # 🚀 ALWAYS FETCH BITGET FUTURES BALANCE
        bal = await asyncio.to_thread(
            exchange.fetch_balance,
            {"type": "swap"}
        )

        # ---------------------------
        # BITGET FUTURES PARSING FIX
        # ---------------------------
        # Correct location for USDT futures balance:
        # bal["info"]["data"]["usdtVo"]["available"]
        if "info" in bal:
            data = bal["info"].get("data", {})
            usdtVo = data.get("usdtVo", {})
            available = usdtVo.get("available", None)

            if available is not None:
                return float(available)

        # ---------------------------
        # FALLBACK (rare cases)
        # ---------------------------
        if "USDT" in bal and isinstance(bal["USDT"], dict):
            if "free" in bal["USDT"]:
                return float(bal["USDT"]["free"])
            if "total" in bal["USDT"]:
                return float(bal["USDT"]["total"])

        return 0.0

    except Exception as e:
        print(f"BALANCE ERROR: {e}")
        return 0.0


# =====================================================
# FETCH PRICE (FUTURES)
# =====================================================
async def get_price(exchange, pair: str) -> float:
    try:
        ticker = await asyncio.to_thread(exchange.fetch_ticker, pair)
        return float(ticker["last"])
    except:
        return 0.0


# =====================================================
# AGGRESSIVE GRID DECISION LOGIC
# =====================================================
def check_grid_signal(price, balance):
    """
    Returns: "LONG", "SHORT", "HOLD"
    """

    if balance <= 0:
        return "HOLD"

    # --- AGGRESSIVE SAMPLE LOGIC ---
    import random
    r = random.random()

    if r < 0.33:
        return "LONG"
    elif r < 0.66:
        return "SHORT"
    else:
        return "HOLD"


# =====================================================
# EXECUTE ORDER (LIVE ONLY)
# =====================================================
async def execute_order(exchange, pair, signal, balance):
    if not config.LIVE_TRADING:
        print(f"[SIMULATION] {signal} — {pair}")
        return

    try:
        # ⚠️ POSITION SIZE = % of capital
        qty = balance * (config.MAX_CAPITAL_PCT / 100)

        if qty <= 0:
            print("NO CAPITAL AVAILABLE")
            return

        if signal == "LONG":
            await asyncio.to_thread(
                exchange.create_market_buy_order, pair, qty
            )

        if signal == "SHORT":
            await asyncio.to_thread(
                exchange.create_market_sell_order, pair, qty
            )

        print(f"[LIVE TRADE] {signal} — {pair} — qty={qty}")

    except Exception as e:
        print(f"[EXECUTION ERROR] {e}")
