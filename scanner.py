# scanner.py
async def scan_symbols(grid):
    """Used by /scan command"""
    data = await grid.scan_all()

    msg = f"SCAN DEBUG — BALANCE: {data['balance']:.2f} USDT\n\n"
    for line in data["lines"]:
        msg += line + "\n"

    return msg
