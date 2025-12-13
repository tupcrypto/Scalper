# exchanges.py
import os
import asyncio
import ccxt.async_support as ccxt
from typing import Optional

import config

async def create_exchange(exchange_id: Optional[str] = None):
    """
    Create & return an async ccxt exchange instance and load markets.
    Returns (exchange, error_message). If no error_message -> success.
    Caller MUST call await exchange.close() when done (we keep long-lived instance).
    """
    eid = (exchange_id or config.EXCHANGE_ID).strip()
    if not eid:
        return None, "EXCHANGE_ID not set in env"

    if not hasattr(ccxt, eid):
        available = ", ".join(sorted(ccxt.exchanges))
        return None, f"ccxt does not list '{eid}' in this environment. Available: {available}"

    cls = getattr(ccxt, eid)
    params = {}
    if config.API_KEY:
        params.update({
            "apiKey": config.API_KEY,
            "secret": config.API_SECRET or "",
        })
    # password/passphrase (some exchanges require)
    if config.API_PASSWORD:
        params["password"] = config.API_PASSWORD

    try:
        exchange = cls(params)
        # try to set default type if futures/swap supported
        try:
            exchange.options["defaultType"] = "swap"
        except Exception:
            pass

        await exchange.load_markets()
        return exchange, None
    except Exception as e:
        try:
            await exchange.close()
        except Exception:
            pass
        return None, f"Exchange init failed: {repr(e)}"
