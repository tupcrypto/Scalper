# blofin_api.py
import ccxt.async_support as ccxt
import asyncio
from decimal import Decimal, ROUND_DOWN
import logging

logger = logging.getLogger("scalper.blofin")

class BlofinAsync:
    def __init__(self, api_key: str, api_secret: str, password: str = ""):
        opts = {"enableRateLimit": True}
        if password:
            opts["password"] = password
        self.exchange = ccxt.blofin({"apiKey": api_key, "secret": api_secret, **opts})

    async def load(self):
        # load markets
        await self.exchange.load_markets()

    async def fetch_balance(self):
        return await self.exchange.fetch_balance()

    async def fetch_ticker(self, symbol: str):
        # return last price or raise
        t = await self.exchange.fetch_ticker(symbol)
        return t

    async def fetch_markets_info(self, symbols: list):
        await self.exchange.load_markets()
        out = []
        for s in symbols:
            if s in self.exchange.markets:
                m = self.exchange.markets[s]
                out.append(f"{s}: base={m.get('base')}, quote={m.get('quote')}, type={m.get('type')}")
            else:
                out.append(f"{s}: NOT FOUND")
        return out

    async def place_market_order(self, symbol: str, side: str, cost_usdt: float):
        # For most exchanges we compute base amount = cost / price for buys.
        ticker = await self.fetch_ticker(symbol)
        price = Decimal(str(ticker.get("last") or ticker.get("close") or 0))
        if price == 0:
            raise RuntimeError("Price is zero")

        # compute base amount
        amount = (Decimal(str(cost_usdt)) / price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)

        # attempt market order:
        try:
            # many ccxt implementations accept amount for market orders (base amount)
            res = await self.exchange.create_order(symbol, "market", side, float(amount), None, {})
            return res
        except Exception as e:
            # return the exception so caller can decide
            logger.exception("order error")
            raise

    async def close(self):
        try:
            await self.exchange.close()
        except Exception:
            logger.exception("Error closing exchange")

