# grid_engine.py
# Full file - exchange helpers for the bot.

import ccxt
import time
import math
from decimal import Decimal, InvalidOperation
import logging
import config

log = logging.getLogger("grid_engine")
log.setLevel(logging.DEBUG if config.VERBOSE else logging.INFO)

def get_exchange():
    """
    Returns a ccxt exchange instance configured with keys from config.
    This is synchronous (ccxt.sync).
    """
    ex_id = config.EXCHANGE_ID
    if not ex_id:
        raise RuntimeError("EXCHANGE_ID not set in config.py or env")

    if ex_id not in ccxt.exchanges:
        raise RuntimeError(f"ccxt does not list '{ex_id}' in this environment. Available: {', '.join(ccxt.exchanges)}")

    ExchangeClass = getattr(ccxt, ex_id)
    opts = {}
    if config.CREATE_MARKET_BUY_REQUIRES_PRICE:
        opts["createMarketBuyOrderRequiresPrice"] = True

    # merge in extras from config.EXCHANGE_EXTRA (empty dict by default)
    opts.update(config.EXCHANGE_EXTRA or {})

    exchange = ExchangeClass({
        "apiKey": config.EXCHANGE_API_KEY,
        "secret": config.EXCHANGE_API_SECRET,
        "password": config.EXCHANGE_API_PASSPHRASE or None,
        "enableRateLimit": True,
        **opts,
    })
    # Optional: set verbose exchange-level logging
    # exchange.verbose = True
    return exchange

def safe_decimal(x):
    try:
        return Decimal(str(x))
    except (InvalidOperation, TypeError):
        return Decimal("0")

def get_assumed_balance(exchange, quote_asset=None):
    """
    Fetch balance and return available quote asset amount (e.g., USDT).
    Uses synchronous fetch_balance; caller should call in executor (asyncio.to_thread).
    """
    quote = quote_asset or config.QUOTE_ASSET
    bal = exchange.fetch_balance()
    # Some exchanges return futures balances under ['info'] or under ['total'] / ['free'] / ['used']
    # We'll try common places.
    # Try futures first (if exchange supports 'info' key with 'positions' etc).
    amount = 0
    # prefer free quote balance
    if isinstance(bal, dict):
        # many ccxt builds return {'total': {...}, 'free': {...}}
        for key in ("free", "total", "info"):
            if key in bal and isinstance(bal[key], dict):
                bucket = bal[key]
                if quote in bucket:
                    amount = bucket[quote]
                    break
        # fallback: top-level key equal to the symbol
        if amount == 0:
            if quote in bal:
                try:
                    amount = bal[quote]
                except Exception:
                    amount = 0

    try:
        return float(amount or 0.0)
    except Exception:
        return 0.0

def fetch_price(exchange, symbol):
    """
    Fetch latest mid/last price for symbol using ticker if available.
    Synchronous; caller should run in executor.
    """
    try:
        ticker = exchange.fetch_ticker(symbol)
        # ticker may have 'last' or 'close'
        p = ticker.get("last") or ticker.get("close") or ticker.get("price") or ticker.get("bid")
        if p is None:
            # some exchanges return string price inside ticker['info']
            p = ticker.get("info", {}).get("lastPrice") or ticker.get("info", {}).get("price")
        return float(p) if p is not None else None
    except Exception as e:
        log.exception("fetch_price error for %s: %s", symbol, e)
        return None

def calculate_amount_for_market(balance_quote, price, allocation=config.ALLOCATION_PER_PAIR, leverage=None):
    """
    Given quote balance (e.g., USDT) and price, compute base-asset amount to buy.
    Return float amount (in base currency).
    """
    try:
        bal = Decimal(str(balance_quote))
        allocation = Decimal(str(allocation))
        price_d = Decimal(str(price))
        if price_d <= 0 or bal <= 0:
            return 0.0
        use = bal * allocation
        # If leverage (futures) is provided, effective buying power grows:
        if leverage and int(leverage) > 1:
            use = use * Decimal(int(leverage))
        amount_base = (use / price_d)
        # round down to sensible precision - many exchanges reject too many decimals
        # We'll return a float; caller should format if specific precision required.
        return float(amount_base)
    except Exception as e:
        log.exception("calculate_amount error: %s", e)
        return 0.0

def execute_order(exchange, symbol, side, amount, price=None, order_type="market"):
    """
    Execute order (synchronous). For market orders, price is typically None.
    Returns exchange.create_order result or raises.
    """
    # Safety: if LIVE_TRADING is False, don't actually send the order.
    if not config.LIVE_TRADING:
        log.info(f"SIMULATION mode: would place {side} {symbol} amount={amount} price={price} type={order_type}")
        return {"simulated": True, "symbol": symbol, "side": side, "amount": amount, "price": price, "type": order_type}

    if amount is None or amount <= 0:
        raise ValueError("Amount must be > 0 to execute order")

    # Many exchanges want 'amount' in base asset for market orders.
    # Others (some derivatives) want cost in quote currency. We try base-asset approach by default.
    try:
        if order_type == "market":
            # For some exchanges, create_market_buy_order requires price to compute cost.
            # We rely on ccxt wrapper; pass amount and type 'market'.
            order = exchange.create_order(symbol, "market", side, amount)
        else:
            # limit order
            if price is None:
                raise ValueError("limit orders require price")
            order = exchange.create_order(symbol, "limit", side, amount, price)
        return order
    except Exception as e:
        # bubble up for caller to log & react to
        raise


