"""
Grid engine and exchange helpers.
Synchronous ccxt usage. Called via run_in_executor from bot (async context).
"""

import ccxt
import math
import time
import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


def get_exchange(api_key: str, api_secret: str):
    """
    Return a ccxt exchange instance configured for Toobit.
    If Toobit isn't available in your ccxt build, you can replace 'toobit' with the correct id.
    """
    # Exchange id: 'toobit' — adjust if your ccxt doesn't have it (check ccxt.exchanges)
    ex_id = "toobit"
    if ex_id not in ccxt.exchanges:
        # fall back to generic unified if necessary (user must confirm)
        raise RuntimeError(f"ccxt does not list '{ex_id}' in this environment. Available: {', '.join(ccxt.exchanges)}")

    exchange_class = getattr(ccxt, ex_id)
    ex = exchange_class({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
        # Some exchanges require extra options; uncomment/adjust if needed:
        # "options": { "createMarketBuyOrderRequiresPrice": False }
    })
    # Set default timeouts
    ex.timeout = 20000
    return ex


def fetch_usdt_futures_balance(exchange):
    """
    Attempts to fetch the USDT futures available balance.
    This is best-effort: many exchanges return different keys.
    Returns float USDT available (not None).
    """
    try:
        bal = exchange.fetch_balance()
    except Exception as e:
        logger.exception("fetch_balance failed")
        raise

    # Many exchanges return 'total'/'free' under nested keys. Try common patterns.
    # 1) futures account breakdown
    for maybe in ("USDT", "USDT:USDT", "USDT-FUTURES"):
        try:
            # check nested dict structures
            if maybe in bal:
                if isinstance(bal[maybe], dict):
                    free = bal[maybe].get("free") or bal[maybe].get("available") or bal[maybe].get("total")
                    if free is not None:
                        return float(free)
                else:
                    # sometimes direct numeric
                    return float(bal[maybe])
        except Exception:
            continue

    # 2) unified structure: bal['total']['USDT']
    try:
        total = bal.get("total", {})
        if isinstance(total, dict) and "USDT" in total:
            return float(total["USDT"])
    except Exception:
        pass

    # 3) fallback: 'free' top-level
    try:
        free = bal.get("free", {})
        if isinstance(free, dict) and "USDT" in free:
            return float(free["USDT"])
    except Exception:
        pass

    # 4) try to find any numeric USDT-like key
    for k, v in bal.items():
        if isinstance(k, str) and "USDT" in k.upper():
            try:
                return float(v.get("free") or v.get("available") or v.get("total") or v)
            except Exception:
                continue

    # last fallback: sum of free values if any numeric
    try:
        if isinstance(bal, dict):
            for part in ("info", "total", "free", "used"):
                if part in bal and isinstance(bal[part], dict) and "USDT" in bal[part]:
                    return float(bal[part]["USDT"])
    except Exception:
        pass

    # can't locate: return 0.0 as safe default (caller should treat 0 as insufficient)
    return 0.0


def symbol_to_ccxt(symbol: str):
    """ normalize symbol like BTC/USDT """
    return symbol.replace("/", "/")


def compute_order_amount(exchange, symbol: str, usdt_budget: float, leverage: int):
    """
    Compute base currency amount to spend for market order given USDT budget and symbol price.
    Returns amount in base currency (float).
    """
    ticker = exchange.fetch_ticker(symbol)
    price = float(ticker["last"] or ticker["close"] or ticker["bid"] or ticker["ask"])
    if price <= 0:
        raise RuntimeError("Invalid price fetched")
    # For futures, approximate notional = amount * price / leverage? If using cross margin with leverage,
    # many exchanges expect margin amount; but we'll compute base amount for a position size = (usdt_budget * leverage) / price
    position_size = (usdt_budget * leverage) / price
    # round down to exchange precision
    market = exchange.market(symbol)
    precision = market.get("precision", {}).get("amount", 8)
    # floor to precision
    factor = 10 ** precision
    amount = math.floor(position_size * factor) / factor
    return amount


def place_market_order(exchange, symbol: str, side: str, amount: float):
    """
    Place a market order. This function tries to handle exchanges that require different params.
    Returns order dict on success or raises.
    """
    try:
        # Use unified create_order interface
        # Some exchanges require specifying 'params' like {"reduceOnly": False, "positionSide": "BOTH"}
        order = exchange.create_order(symbol, "market", side.lower(), amount)
        return order
    except Exception as e:
        # Try fallback for exchanges that require market buy amount as cost
        # We'll attempt to calculate cost and pass as amount param for buy on such exchanges
        try:
            # fetch price
            ticker = exchange.fetch_ticker(symbol)
            price = float(ticker.get("last") or ticker.get("close") or ticker.get("ask") or ticker.get("bid"))
            if side.lower() == "buy":
                # amount might be interpreted as cost on some exchanges — attempt to pass cost instead
                cost = amount * price
                # Some exchanges accept create_market_buy_order_requires_price option — try using create_order with cost
                order = exchange.create_order(symbol, "market", side.lower(), None, cost)
                return order
        except Exception:
            pass
        raise


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0

