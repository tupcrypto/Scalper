# grid_engine.py
import asyncio
from decimal import Decimal, InvalidOperation

class GridManager:
    def __init__(self, exchange, symbols):
        self.exchange = exchange
        self.symbols = symbols
        self.tasks = {}

    async def get_price(self, symbol):
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker.get("last") or ticker.get("close") or None
        except Exception as e:
            return None

    async def get_balance_usdt(self):
        try:
            bal = await self.exchange.fetch_balance()
            # try common keys
            for key in ("USDT", "usdt"):
                if key in bal and isinstance(bal[key], dict):
                    return float(bal[key].get("free", 0) or 0)
            # fallback: try total['free'] for any USDT field
            for k, v in bal.items():
                if k and "USDT" in str(k).upper() and isinstance(v, dict):
                    return float(v.get("free", 0) or 0)
            # fallback total
            return float(bal.get("total", {}).get("USDT", 0) or 0)
        except Exception:
            return 0.0

    async def start_grid_for(self, symbol, loop_seconds=10, notify=None):
        """
        start a non-blocking background loop for a symbol.
        notify(bot, text) is optional callback to send messages
        """
        if symbol in self.tasks:
            return False  # already running

        async def _loop():
            while True:
                price = await self.get_price(symbol)
                bal = await self.get_balance_usdt()
                msg = f"[GRID] {symbol} price={price} balance={bal}"
                print(msg)
                if notify:
                    try:
                        await notify(msg)
                    except Exception:
                        pass
                await asyncio.sleep(loop_seconds)

        task = asyncio.create_task(_loop())
        self.tasks[symbol] = task
        return True

    async def stop_all(self):
        for t in list(self.tasks.values()):
            t.cancel()
        self.tasks = {}
        try:
            await self.exchange.close()
        except Exception:
            pass
