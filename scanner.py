async def scan_symbols(grid):
    balance = await grid.exchange.fetch_balance()
    bal = balance.get("USDT", {}).get("free", 0)

    result = f"SCAN DEBUG — BALANCE: {bal:.2f} USDT\n\n"

    for sym in grid.symbols:
        price = await grid.get_price(sym)

        if price is None:
            result += f"{sym}: ERROR price unavailable\n"
        else:
            result += f"{sym}: price = {price}\n"

    return result
