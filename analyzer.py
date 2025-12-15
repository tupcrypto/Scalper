import requests
from config import OPENROUTER_API_KEY

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def analyze_sync(symbol, price):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        # 🔥 FAST + STABLE MODEL
        "model": "mistralai/mistral-7b-instruct",
        "temperature": 0.2,
        "max_tokens": 350,
        "messages": [
            {
                "role": "user",
                "content": f"""
You are an elite crypto futures trader.

Analyze {symbol} on 15m + 1h timeframe.
Current price: {price}

Give:
Upside Probability (%)
Downside Probability (%)
Flat Probability (%)

If highest probability >= 75%:
- Direction (LONG or SHORT)
- Entry
- Stop Loss
- Take Profit

Be strict. Avoid bad trades.
"""
            }
        ],
    }

    try:
        r = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=20  # 🔥 HARD TIMEOUT
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    except Exception as e:
        return f"❌ AI analysis failed: {str(e)}"
