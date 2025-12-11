# grid_engine.py
import os
import asyncio
import logging
from decimal import Decimal, InvalidOperation, ROUND_DOWN, getcontext

import ccxt.async_support as ccxt

from typing import Dict, Any, Optional
import config

getcontext().prec = 18

LOG = logging.getLogger("grid_engine")

# Build exchange client (async)
async def get_exchange():
    ex_id = config.EXCHANGE_ID
    apiKey = os.getenv("EXCHANGE_API_KEY", config.EXCHANGE_API_KEY)
    secret = os.getenv("EXCHANGE_API_SECRET", config.EXCHANGE_API_SECRET)
    password = os.getenv("EXCHANGE_API_PASSWORD", config.EXCHANGE_API_PASSWORD)

    if not apiKey or not secret:
        raise RuntimeError("Exchange API key/secret are not set in env")

    # instantiate
    exchange_class = getattr(ccxt, ex_id, None)
    if exchange_class is None:
        # ccxt provides exchange in ccxt.<id>; but safe fallback
        try:
            exchange_class = ccxt.__dict__[ex_id]
        except Exception:
            raise RuntimeError(f"ccxt does not list '{ex_id}' in this environment. Available: {', '.join(sorted(ccxt.exchanges))}")

    exchange = exchange_class({
        "apiKey": apiKey,
        "secret": secret,
        "password": password,
        "enableRateLimit": True,
        # avoid aggressive timeouts
        "timeout": 20000,
        "options": {
            # default: use limit orders to be broadly compatible
            "createMarketBuyOrderRequiresPrice": False,
        },
    })

    # Optionally, if BloFin test host is required uncomment and set url
    # if ex_id == "blofin" and os.getenv("BLOFIN_USE_DEMO", "false").lower() in ("1","true"):
    #     exchange.urls['api'] = {'rest': 'https://demo-trading-openapi.blofin.com'}

    await exchange.load_markets()
    LOG.info("Exchange loaded: %s", ex_id)
    return exchange

# Safe helper to get USDT futures balance (tries common shapes)
async def fetch_usdt_balance(exchange) -> float:
    try:
        bal = await exchange.fetch_balance(params={})
        # ccxt often returns balances under 'total'
        # we try multiple locations
        for key in ("USDT", "TUSD", "USD"):
            if isinstance(bal, dict) and key in bal:
                sub = bal[key]
                if isinstance(sub, dict):
                    val = sub.get("total") or sub.get("free") or sub.get("used")
                    if val is not None:
                        return float(val)
        # fallback: try top-level 'total' mapping
        total = bal.get("total") if isinstance(bal, dict) else None
        if isinstance(total, dict):
            for k in ("USDT", "USD", "TUSD"):
                if k in total and total[k] is not None:
                    return float(total[k])
        # sometimes fetch_balance returns a float or nested structure
        # as final fallback, try to find any 'USDT' in json string
        if isinstance(bal, dict):
            if "info" in bal and isinstance(bal["info"], dict):
                # market-specific structures (best effort)
                info = bal["info"]
                # try common paths
                for path in ("availableMargin", "totalBalance", "usdtBalance", "balance"):
                    if path in info:
                        try:
                            return float(info[path])
                        except Exception:
                            pass
        LOG.debug("fetch_balance raw: %s", bal)
    except Exception as e:
        LOG.exception("fetch_usdt_balance error: %s", e)
    return 0.0

# Helper: fetch ticker price
async def fetch_price(exchange, symbol: str) -> Optional[float]:
    try:
        ticker = await exchange.fetch_ticker(symbol)
        price = ticker.get("last") if isinstance(ticker, dict) else None
        return float(price) if price is not None else None
    except Exception as e:
        LOG.debug("fetch_price error for %s: %s", symbol, e)
        return None

# Determine how much USDT to spend per trade
def compute_usdt_spend(total_usdt: float) -> float:
    spend = total_usdt * float(config.MAX_BALANCE_USAGE_PCT)
    # ensure at least MIN_ORDER_USDT
    if spend < config.MIN_ORDER_USDT:
        return 0.0
    return float(spend)

# Create a limit order with a small price offset (avoids market-order API differences)
async def place_limit_order(exchange, symbol: str, side: str, usdt_amount: float, price: float, params: Optional[dict] = None) -> Dict[str, Any]:
    """
    side: 'buy' or 'sell'
    usdt_amount: how much quote currency (USDT) to spend (for buys) or receive (for sells)
    price: limit price (in quote per base)
    Returns ccxt order response or raises
    """
    params = params or {}
    try:
        # compute base amount = usdt_amount / price
        amount = Decimal(str(usdt_amount)) / Decimal(str(price))
        # many exchanges require rounding to market precision; attempt safe rounding
        markets = exchange.markets
        market = markets.get(symbol)
        if market:
            precision = market.get("precision", {}).get("amount")
            if precision is not None:
                quant = Decimal(1) / (Decimal(10) ** Decimal(precision))
                amount = (amount // quant) * quant
        # final float
        amount_f = float(amount)
        if amount_f <= 0:
            raise RuntimeError("Computed order amount <= 0")

        LOG.info("Placing LIMIT %s %s @ %s amount=%s (usdt=%s)", side.upper(), symbol, price, amount_f, usdt_amount)
        order = await exchange.create_order(symbol, "limit", side, amount_f, price, params)
        return order
    except InvalidOperation as e:
        LOG.exception("Decimal error when computing order amount: %s", e)
        raise
    except Exception as e:
        LOG.exception("place_limit_order failed: %s", e)
        raise

# Close exchange connections cleanly
async def close_exchange(exchange):
    try:
        await exchange.close()
    except Exception:
        pass


