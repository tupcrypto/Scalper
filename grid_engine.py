import asyncio

class GridManager:
    def __init__(self, exchange, symbols, bot):
        self.exchange = exchange
        self.symbols = symbols
        self.bot = bot

    async def get_price(self, symbol):
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker.get("last")
        except:
            return None

    async def run_grid_loop(self, symbol):
        while True:
            price = await self.get_price(symbol)

            if price is None:
                print(f"[GRID ERROR] price unavailable for {symbol}")
            else:
                print(f"[GRID] {symbol}: {price}")

            await asyncio.sleep(10)  # prevent blocking

