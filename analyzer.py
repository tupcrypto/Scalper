import requests
from config import OPENROUTER_API_KEY
from prompts import analysis_prompt

def analyze_sync(symbol, price):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openrouter/auto",
        "messages": [
            {"role": "user", "content": analysis_prompt(symbol, price)}
        ]
    }

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )

    return r.json()["choices"][0]["message"]["content"]
