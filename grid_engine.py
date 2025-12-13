import math
import time
import config

class NeutralGrid:
    def __init__(self, exchange):
        self.ex = exchange
        self.running = False

    def get_price(self, symbol):
        ticker = self.ex.fetch_ticker(symbol)
        return ticker["last"]

    def set_leverage(self, symbol):
        try:
            self.ex.set_leverage(config.LEVERAGE, symbol)
        except Exception:
            pass

    def build_grid(self, price):
        half_range = price * config.GRID_RANGE_PERCENT / 100
        low = price - half_range
        high = price + half_range
        step = (high - low) / config.GRID_LEVELS
        return [low + i * step for i in range(config.GRID_LEVELS + 1)]

    def place_order(self, symbol, side, price):
        if not config.EXECUTE_ORDERS:
            return

        amount = round(config.USDT_PER_GRID / price, 6)
        self.ex.create_limit_order(symbol, side, amount, price)

    def run(self):
        self.running = True
        while self.running:
            for symbol in config.PAIRS:
                try:
                    self.set_leverage(symbol)
                    price = self.get_price(symbol)
                    grid = self.build_grid(price)

                    for g in grid:
                        if g < price:
                            self.place_order(symbol, "buy", g)
                        elif g > price:
                            self.place_order(symbol, "sell", g)

                except Exception as e:
                    print(f"[GRID ERROR] {symbol}: {e}")

            time.sleep(config.GRID_LOOP_SECONDS)

    def stop(self):
        self.running = False

