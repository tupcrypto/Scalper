# grid_engine.py

import asyncio
import logging
import config

logger = logging.getLogger("grid")


class GridManager:

    def __init__(self, exchange, symbols, bot):
        self.exchange = exchange
        self.symbols = symbols
        self.bot = bot
        self.markets_loaded = False
        self.markets = {}

    async def load_markets(self):
        if not self.markets_loaded:
            try:
                self.markets = await self.exchange.load_markets()
                self.markets_loaded = True
                logger.info("Blofin markets loaded.")
            except Exception as e:
                logger.error(f"Market load error: {e}")

    async def price(self, symbol):
        try:
            t = await self.exchange.fetch_ticker(symbol)
            return t["last"]
        except Exception as e:
            logger.error(f"Ticker error {symbol}: {e}")
            return None

    async def balance(self):
        try:
            b = await self.exchange.fetch_balance()
            usdt = float(b.get("USDT", {}).get("free", 0.0))
            return usdt
        except Exception as e:
            logger.error(f"Balance error: {e}")
            return 0.0

    async def scan_all(self):
        await self.load_markets()
        balance = await self.balance()
        lines = []

        for sym in self.symbols:
            px = await self.price(sym)
            if px is None:
                lines.append(f"{sym}: ERROR price unavailable")
            else:
                lines.append(f"{sym}: price={px}")

        return {"balance": balance, "lines": lines}

    async def make_order(self, sym, side, price):
        try:
            market = self.exchange.market(sym)

            qty = config.MIN_ORDER_USDT / price
            qty = float(self.exchange.amount_to_precision(sym, qty))

            order = await self.exchange.create_order(
                symbol=sym,
                type="market",
                side=side,
                amount=qty
            )

            logger.info(f"ORDER SUCCESS {sym} {side} {qty}")
            return order

        except Exception as e:
            logger.error(f"Order error {sym}: {e}")
            return None

    async def run_grid_loop(self, symbol):
        await self.load_markets()

        while True:
            try:
                price = await self.price(symbol)
                if price is None:
                    await asyncio.sleep(config.GRID_LOOP_SECONDS)
                    continue

                balance = await self.balance()
                if balance < config.MIN_ORDER_USDT:
                    logger.info(f"[GRID] {symbol} — NO ORDER @ {price} — balance too low")
                    await asyncio.sleep(config.GRID_LOOP_SECONDS)
                    continue

                fraction = (price % 1)

                if fraction < 0.25:
                    logger.info(f"[GRID] BUY {symbol} @ {price}")
                    await self.make_order(symbol, "buy", price)

                elif fraction > 0.75:
                    logger.info(f"[GRID] SELL {symbol} @ {price}")
                    await self.make_order(symbol, "sell", price)

                await asyncio.sleep(config.GRID_LOOP_SECONDS)

            except Exception as e:
                logger.error(f"[GRID LOOP ERROR] {e}")
                await asyncio.sleep(config.GRID_LOOP_SECONDS)

