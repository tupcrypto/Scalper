# grid_engine.py  (FULL replacement)
import ccxt.async_support as ccxt
import asyncio
import math
import config
import time

# Single shared exchange instance (created on first call)
_EXCHANGE = None

def _normalize_pair_for_bitget(pair: str) -> str:
    # ccxt/bitget futures often use "BTC/USDT:USDT" format for swap markets.
    # We accept "BTC/USDT" in config and convert to "BTC/USDT:USDT"
    if ":" in pair:
        return pair
    return f"{pair}:USDT"

async def get_exchange():
    """
    Returns a shared ccxt async exchange instance configured for Bitget USDT-M swap.
    """
    global _EXCHANGE
    if _EXCHANGE is not None:
        return _EXCHANGE

    exchange = ccxt.bitget({
        "apiKey": config.BITGET_API_KEY,
        "secret": config.BITGET_API_SECRET,
        "password": config.BITGET_PASSPHRASE,
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",  # make sure we talk to USDT-perpetual endpoints
            "createMarketBuyOrderRequiresPrice": False,
        }
    })

    # small safety config
    exchange.headers = {"User-Agent": "XLR8-BOT/1.0"}
    _EXCHANGE = exchange
    return _EXCHANGE

# -----------------------
# BALANCE PARSER (robust)
# -----------------------
async def get_balance(exchange):
    """
    Try multiple paths inside Bitget fetch_balance() result to find USDT futures available balance.
    Returns float (USDT).
    """
    try:
        # force swap/futures type - many ccxt builds accept this param
        balance = await exchange.fetch_balance({"type": "swap"})
    except Exception:
        # fallback without type
        try:
            balance = await exchange.fetch_balance()
        except Exception as e:
            # can't fetch balance
            return 0.0

    # Try multiple likely locations
    try:
        # 1) Common Bitget structure: balance['info']['USDT']['available']
        usdt = None
        info = balance.get("info", {})
        if isinstance(info, dict):
            usdt = info.get("USDT", {}).get("available") or info.get("usdt", {}).get("available") if isinstance(info.get("USDT", {}), dict) else None

        # 2) ccxt often maps top-level 'USDT' key
        if usdt is None:
            top = balance.get("USDT")
            if isinstance(top, dict):
                usdt = top.get("free") or top.get("available") or top.get("total")

        # 3) ccxt older: balance['total'].get('USDT')
        if usdt is None:
            total = balance.get("total", {})
            if isinstance(total, dict):
                usdt = total.get("USDT") or total.get("USDT")
                # some ccxt returns numeric directly
        # 4) fallback: try 'info' deeper keys
        if usdt is None and isinstance(info, dict):
            # sometimes info contains nested dicts under keys like 'data' or 'result'
            for k in ("data", "result"):
                if k in info and isinstance(info[k], dict):
                    candidate = info[k].get("USDT") or info[k].get("usdt")
                    if isinstance(candidate, dict):
                        usdt = candidate.get("available") or candidate.get("free") or candidate.get("total")
                        if usdt:
                            break

        # final fallback checks
        if usdt is None:
            # try safe keys
            usdt = 0.0
            possible = balance.get("free") or balance.get("free", {})
            if isinstance(possible, dict):
                usdt = possible.get("USDT", 0.0)

        # convert safely
        return float(usdt or 0.0)
    except Exception:
        return 0.0

# -----------------------
# FETCH PRICE
# -----------------------
async def get_price(exchange, pair):
    bitget_symbol = _normalize_pair_for_bitget(pair)
    ticker = await exchange.fetch_ticker(bitget_symbol)
    return float(ticker.get("last", 0.0) or 0.0)

# -----------------------
# SIMPLE DECISION (safe)
# -----------------------
async def decide_action(exchange, pair):
    """
    Lightweight decision engine:
    - fetch 3 x 1m candles and decide momentum.
    - If latest close is lower than average (downward momentum) -> LONG (buy dip)
    - If latest close is higher than average (up momentum) -> SHORT (sell rise)
    This is a simple heuristic for demonstration; you can replace it later with better logic.
    """
    bitget_symbol = _normalize_pair_for_bitget(pair)
    try:
        ohlcv = await exchange.fetch_ohlcv(bitget_symbol, timeframe="1m", limit=5)
        if not ohlcv or len(ohlcv) < 3:
            return "HOLD"
        closes = [c[4] for c in ohlcv if len(c) >= 5]
        avg = sum(closes[:-1]) / max(1, len(closes[:-1]))
        last = closes[-1]
        # momentum percentage
        diff = (last - avg) / avg if avg != 0 else 0
        # thresholds
        if diff < -0.0015:       # small dip -> consider LONG (buy the dip)
            return "LONG"
        elif diff > 0.0015:      # small rise -> consider SHORT (sell into strength)
            return "SHORT"
        else:
            return "HOLD"
    except Exception:
        return "HOLD"

# -----------------------
# ORDER EXECUTOR (safe)
# -----------------------
async def execute_order(exchange, pair, side, usdt_cost):
    """
    Execute an order.
    By default, this function simulates unless config.LIVE_TRADING == True.
    For Bitget: we will attempt to use market order with amount=cost (ccxt option set).
    """
    bitget_symbol = _normalize_pair_for_bitget(pair)
    min_order = config.get_min_order_for_pair(pair)
    if usdt_cost < min_order:
        return {"ok": False, "error": f"order cost {usdt_cost:.2f} < min {min_order:.2f}"}

    if not config.LIVE_TRADING:
        return {"ok": True, "sim": True, "side": side, "cost": usdt_cost}

    try:
        # Many CCXT bitget implementations expect amount as base size for market orders.
        # Because Bitget/ccxt mapping varies, we attempt to create market order with 'amount' as cost.
        # If that fails, we will calculate quantity = cost / price and try again.
        try:
            # first attempt: pass cost as amount
            order = await exchange.create_order(
                symbol=bitget_symbol,
                type="market",
                side=side.lower(),
                amount=float(usdt_cost),
                params={}
            )
            return {"ok": True, "order": order}
        except Exception as e1:
            # fallback: compute qty = cost / price then place market order with qty
            ticker = await exchange.fetch_ticker(bitget_symbol)
            price = float(ticker.get("last", 0.0) or 0.0)
            if price <= 0:
                return {"ok": False, "error": "invalid price for qty calc"}
            qty = usdt_cost / price
            order = await exchange.create_order(
                symbol=bitget_symbol,
                type="market",
                side=side.lower(),
                amount=float(qty),
                params={}
            )
            return {"ok": True, "order": order}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# -----------------------
# PROCESS ONE SYMBOL (main entry used by bot)
# -----------------------
async def process_symbol(exchange, pair, balance):
    """
    - pair: "BTC/USDT"
    - balance: float USDT available in futures wallet
    """
    try:
        price = await get_price(exchange, pair)
    except Exception as e:
        return {"action": "ERROR", "price": 0, "result": f"price error: {e}"}

    min_order = config.get_min_order_for_pair(pair)
    if balance < min_order:
        return {"action": "NO_ORDER", "price": price, "result": f"Balance {balance:.2f} too small"}

    # determine action
    action = await decide_action(exchange, pair)

    if action == "HOLD":
        return {"action": "HOLD", "price": price, "result": "Neutral zone"}

    # compute allocation: split allowed capital across pairs and grid levels
    try:
        pairs_count = max(1, len(config.PAIRS))
        alloc_total = (balance * (config.MAX_CAPITAL_PCT / 100.0))
        # default allocate equal to each pair, and then divide across grid levels to be conservative
        usdt_alloc = alloc_total / pairs_count / max(1, config.GRID_LEVELS)
        # ensure at least min_order
        usdt_alloc = max(usdt_alloc, min_order)
    except Exception:
        usdt_alloc = max(min_order, balance * 0.01)

    # execute or simulate
    res = await execute_order(await get_exchange(), pair, "buy" if action == "LONG" else "sell", usdt_alloc)

    if res.get("ok"):
        if res.get("sim"):
            return {"action": action, "price": price, "result": f"(SIM) {action} simulated with {usdt_alloc:.2f} USDT"}
        else:
            return {"action": action, "price": price, "result": f"ORDER PLACED: {usdt_alloc:.2f} USDT"}
    else:
        return {"action": "ERROR", "price": price, "result": f"ORDER_FAIL: {res.get('error')}"}

# -----------------------
# CLEANUP (close exchange) - call when shutting down if possible
# -----------------------
async def close_exchange():
    global _EXCHANGE
    try:
        if _EXCHANGE:
            await _EXCHANGE.close()
    except Exception:
        pass
    _EXCHANGE = None

