# grid_engine.py
import ccxt.async_support as ccxt
import asyncio
import logging
from decimal import Decimal, InvalidOperation, ROUND_DOWN

import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_exchange = None
_markets_cache = None


async def get_exchange():
    """Return an initialized ccxt async exchange for the configured EXCHANGE_ID."""
    global _exchange
    if _exchange is None:
        ex_id = config.EXCHANGE_ID
        params = {"apiKey": config.API_KEY, "secret": config.API_SECRET}
        # many exchanges want 'password' credential (passphrase)
        if getattr(config, "API_PASSWORD", None):
            params["password"] = config.API_PASSWORD
        _exchange = getattr(ccxt, ex_id)(params)
        # If FUTURES, enable defaultType fallback
        try:
            _exchange.options = getattr(_exchange, "options", {})
            # some exchanges accept defaultType
            _exchange.options.setdefault("defaultType", "future")
        except Exception:
            pass
        # load markets once
        try:
            await _exchange.load_markets()
        except Exception as e:
            logger.error(f"Exchange init failed: {e}")
    return _exchange


async def close_exchange():
    global _exchange
    if _exchange:
        try:
            await _exchange.close()
        except Exception as e:
            logger.info(f"Error when closing exchange: {e}")
        _exchange = None


async def _ensure_markets():
    global _markets_cache
    if _markets_cache is None:
        ex = await get_exchange()
        if ex is None:
            _markets_cache = {}
            return _markets_cache
        try:
            _markets_cache = await ex.load_markets()
        except Exception as e:
            logger.error(f"load_markets error: {e}")
            _markets_cache = {}
    return _markets_cache


def _find_future_market_for_base(markets, base):
    """Heuristic: find a futures/swap market that has base and USDT quote.
       Returns market symbol string as ccxt uses it (e.g. BTC/USDT:USDT or BTC-USDT).
    """
    base = base.upper()
    # prefer markets with 'future' or 'swap' market type if provided
    candidates = []
    for sym, m in markets.items():
        # symbol examples: 'BTC/USDT:USDT', 'BTC/USDT', 'BTC-USDT', 'BTCUSDT'
        if base not in m.get("symbol", "").upper():
            continue
        quote = (m.get("quote") or "").upper()
        if quote != "USDT":
            continue
        # prefer derivative types
        mtype = m.get("type") or ""
        if mtype in ("swap", "future", "futures"):
            candidates.insert(0, m["symbol"])
        else:
            candidates.append(m["symbol"])
    # fallback: return first candidate
    return candidates[0] if candidates else None


async def get_market_symbol_for_base(base):
    markets = await _ensure_markets()
    return _find_future_market_for_base(markets, base)


async def get_balance():
    """Try to fetch futures balance. Use fallback to normal fetch_balance."""
    ex = await get_exchange()
    if ex is None:
        return 0.0
    try:
        # many ccxt exchanges accept {"type":"future"} or {"type":"futures"}
        for t in ({"type": "future"}, {"type": "futures"}, {"type": "margin"}, None):
            try:
                if t is None:
                    bal = await ex.fetch_balance()
                else:
                    bal = await ex.fetch_balance(params=t)
                # prefer 'USDT' in balances
                total = bal.get("total", {})
                if "USDT" in total:
                    return float(total.get("USDT", 0.0))
                # fallback: return any numeric sum
                # some exchanges return 'USDT' under different key
                for k, v in total.items():
                    try:
                        return float(v)
                    except Exception:
                        continue
            except Exception:
                continue
    except Exception as e:
        logger.error(f"get_balance error: {e}")
    return 0.0


async def get_price(symbol):
    """Fetch last price for a market symbol string used by ccxt."""
    ex = await get_exchange()
    if ex is None:
        return None
    try:
        ticker = await ex.fetch_ticker(symbol)
        return float(ticker.get("last") or ticker.get("close") or 0.0)
    except Exception as e:
        logger.error(f"PRICE ERROR {symbol}: {e}")
        return None


def _quantize_amount(amount, precision=6):
    try:
        d = Decimal(amount).quantize(Decimal(10) ** -precision, rounding=ROUND_DOWN)
        return float(d)
    except (InvalidOperation, Exception):
        return float(round(amount, 6))


async def place_limit_order(symbol, side, price, usdt_size):
    """Place a limit order on futures. amount calculated from usdt_size / price (best effort)."""
    ex = await get_exchange()
    if ex is None:
        raise RuntimeError("Exchange not initialized")
    try:
        # amount calculation: contracts = usdt_size / price
        amount = usdt_size / price if price > 0 else 0
        amount = _quantize_amount(amount, precision=6)
        order = await ex.create_order(symbol, type="limit", side=side, amount=amount, price=price)
        return order
    except Exception as e:
        logger.error(f"ORDER ERROR {symbol} {side} {price} {usdt_size}: {e}")
        raise


async def run_grid_for_symbol(symbol, price):
    """Very simple example neutral grid: place a buy limit slightly below and sell limit slightly above."""
    if price is None:
        logger.info(f"[GRID] {symbol} — price N/A")
        return

    balance = await get_balance()
    if balance < config.ORDER_SIZE_USDT:
        logger.info(f"[GRID] {symbol} — NO ORDER @ {price} — Balance {balance:.2f} too small")
        return

    try:
        buy_price = round(price * 0.997, 6)
        sell_price = round(price * 1.003, 6)

        await place_limit_order(symbol, "buy", buy_price, config.ORDER_SIZE_USDT)
        await place_limit_order(symbol, "sell", sell_price, config.ORDER_SIZE_USDT)

        logger.info(f"[GRID] {symbol} — placed buy@{buy_price} sell@{sell_price}")

    except Exception as e:
        logger.error(f"[GRID ERROR] {symbol}: {e}")


async def get_markets_list():
    ex = await get_exchange()
    if ex is None:
        return []
    try:
        markets = await ex.load_markets()
        return list(markets.keys())
    except Exception as e:
        logger.error(f"MARKETS LIST ERROR: {e}")
        return []
