def analysis_prompt(symbol, price):
    return f"""
You are a world-class crypto futures trader.

Analyze {symbol} using:
- 15m + 1h timeframe confluence
- Market structure
- Momentum
- Liquidity & fakeouts
- Risk management

Current price: {price}

Respond EXACTLY in this format:

Upside Probability: X%
Downside Probability: X%
Flat Probability: X%

Bias: LONG / SHORT / NO TRADE

If highest probability >= 75%, also include:
Entry:
Stop Loss:
Take Profit:

Reject bad trades aggressively.
"""
