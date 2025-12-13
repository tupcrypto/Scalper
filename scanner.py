# scanner.py
async def run_scan(grid: "GridManager"):
    bal = await grid.get_balance_usdt()
    out = f"SCAN DEBUG — BALANCE: {bal:.2f} USDT\n\n"
    for s in grid.symbols:
        price = await grid.get_price(s)
        if price is None:
            out += f"{s}: ERROR price unavailable\n"
        else:
            out += f"{s}: price={price}\n"
    return out
