# grid_engine.py
import asyncio
import logging
from decimal import Decimal
import config

logger = logging.getLogger("scalper.grid")

class GridManager:
    def __init__(self, exchange, symbols, bot):
        self.exchange = exchange
        self.symbols = symbols
        self.bot = bot

    async def run_grid_loop(self, symbol: str):
        """Main loop per symbol."""
        try:
            await self.exchange.load()
        except Exception:
            logger.exception("exchange load failed")

        while True:
            try:
                await asyncio.sleep(config.GRID_LOOP_SECONDS)
                await self._single_iteration(symbol)
            except asyncio.CancelledError:
                logger.info("Grid loop cancelled for %s", symbol)
                break
            except Exception as e:
                logger.exception("[GRID LOOP ERROR] %s", e)
                # keep looping after error
                await asyncio.sleep(3)

    async def _single_iteration(self, symbol: str):
        # fetch balance (assume USDT in futures wallet)
        bal_resp = await self.exchange.fetch_balance()
        # assume 'USDT' exists
        usdt_bal = 0.0
        if isinstance(bal_resp, dict):
            # ccxt structure: {'total': {'USDT': 10.0}, ...}
            total = bal_resp.get("total", {}) or bal_resp.get("free", {})
            usdt_bal = float(total.get("USDT") or total.get("usdt") or 0.0)
        else:
            # fallback
            usdt_bal = 0.0

        lines = []
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            price = ticker.get("last") or ticker.get("close")
        except Exception:
            price = None

        # decide
        if price is None:
            lines.append(f"{symbol}: price=N/A")
            await self._send_log(symbol, f"{symbol} — price N/A")
            return {"status": "no_price", "balance": usdt_bal}

        price = float(price)
        lines.append(f"{symbol}: price={price}")
        # simple neutral rule: if price moved up > 0.6% in last minute -> hold/short candidate (example)
        # For prototype, always show HOLD if small balance
        if usdt_bal < float(config.MIN_ORDER_USDT):
            await self._send_log(symbol, f"[GRID] {symbol} — NO ORDER @ {price}\nBalance {usdt_bal:.2f} too small")
            return {"status": "no_balance", "balance": usdt_bal}

        # If execution allowed, place small market buy to test
        if config.EXECUTE_ORDERS:
            try:
                res = await self.exchange.place_market_order(symbol, "buy", float(config.TRADE_USDT_PER_SYMBOL))
                await self._send_log(symbol, f"[GRID] {symbol} — LONG_ENTRY @ {price}\nORDER RESULT: {res}")
            except Exception as e:
                await self._send_log(symbol, f"ORDER ERROR: {e}")
        else:
            await self._send_log(symbol, f"[GRID] {symbol} — HOLD — Neutral zone\n(Execute disabled; set EXECUTE_ORDERS=true to trade)")

        return {"status": "ok", "balance": usdt_bal}

    async def _send_log(self, symbol: str, msg: str):
        try:
            # send to monitoring chat (first admin chat not stored here) - instead we'll log
            logger.info("[%s] %s", symbol, msg)
        except Exception:
            logger.exception("log send failed")

    async def scan_all(self):
        """Return one-shot scan summary."""
        bal_resp = await self.exchange.fetch_balance()
        total = bal_resp.get("total", {}) if isinstance(bal_resp, dict) else {}
        usdt_bal = float(total.get("USDT") or 0.0)
        lines = []
        for s in self.symbols:
            try:
                t = await self.exchange.fetch_ticker(s)
                price = t.get("last") or t.get("close") or "N/A"
                if price != "N/A":
                    lines.append(f"{s}: price={price}")
                else:
                    lines.append(f"{s}: price=N/A")
            except Exception as e:
                lines.append(f"{s}: ERROR {e}")
        return {"balance": usdt_bal, "lines": lines}
