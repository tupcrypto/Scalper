# test_balance.py
import os
import sys
import time
import json
import decimal
import traceback

try:
    import ccxt
except Exception as e:
    print("ERROR: ccxt not installed. Install with: pip install ccxt")
    raise

def pretty(obj):
    try:
        return json.dumps(obj, indent=2, default=str)
    except Exception:
        return str(obj)

def main():
    key = os.getenv("BITGET_API_KEY", "")
    secret = os.getenv("BITGET_API_SECRET", "")
    passphrase = os.getenv("BITGET_PASSPHRASE", "")

    if not (key and secret):
        print("ERROR: BITGET_API_KEY or BITGET_API_SECRET env var missing.")
        sys.exit(1)

    print("Creating ccxt.bitget exchange object (sync)...")
    exchange = ccxt.bitget({
        'apiKey': key,
        'secret': secret,
        'password': passphrase,   # bitget uses passphrase in some ccxt versions
        'enableRateLimit': True,
        'options': {
            # try both variants (some CCXT versions use 'future', some 'futures' or 'contract')
            'defaultType': 'future',     # try to force futures wallet
            # 'createMarketBuyOrderRequiresPrice': False,  # not setting here, used in order placement
        }
    })

    # print ccxt version and exchange capabilities
    print("ccxt version:", ccxt.__version__)
    print("Exchange id:", exchange.id)
    print("Exchange has:", exchange.has)
    print("Exchange urls:", {k: exchange.urls.get(k) for k in ('api', 'www') if exchange.urls.get(k)})

    # load markets
    try:
        print("\nLoading markets...")
        exchange.load_markets()
        print("Loaded", len(exchange.markets), "markets")
    except Exception as e:
        print("Error loading markets:", e)
        traceback.print_exc()

    # Try multiple fetch_balance attempts - print everything
    print("\n--- Attempt 1: exchange.fetch_balance() ---")
    try:
        bal = exchange.fetch_balance()
        print("fetch_balance() result:")
        print(pretty(bal))
    except Exception as e:
        print("fetch_balance() error:", e)
        traceback.print_exc()

    print("\n--- Attempt 2: exchange.fetch_balance({'type':'future'}) ---")
    try:
        bal2 = exchange.fetch_balance({'type': 'future'})
        print("fetch_balance({'type':'future'}) result:")
        print(pretty(bal2))
    except Exception as e:
        print("fetch_balance({'type':'future'}) error:", e)
        traceback.print_exc()

    print("\n--- Attempt 3: exchange.fetch_balance({'type':'futures'}) ---")
    try:
        bal3 = exchange.fetch_balance({'type': 'futures'})
        print("fetch_balance({'type':'futures'}) result:")
        print(pretty(bal3))
    except Exception as e:
        print("fetch_balance({'type':'futures'}) error:", e)
        traceback.print_exc()

    print("\n--- Attempt 4: exchange.fetchFreeBalance (common helper, if present) ---")
    try:
        if hasattr(exchange, 'fetchFreeBalance'):
            fb = exchange.fetchFreeBalance()
            print("fetchFreeBalance() result:")
            print(pretty(fb))
        else:
            print("fetchFreeBalance not available in this ccxt version.")
    except Exception as e:
        print("fetchFreeBalance error:", e)
        traceback.print_exc()

    print("\n--- Attempt 5: Try fetching position / margin endpoints (raw) ---")
    try:
        # Try known private API endpoints for bitget (ccxt mapping may differ)
        # We'll attempt generic private GET /api/mix/v1/account/accounts or similar if available.
        # This is best-effort and may fail depending on ccxt version; print full exception.
        if hasattr(exchange, 'private_get_account_accounts'):
            raw = exchange.private_get_account_accounts()
            print("private_get_account_accounts()", pretty(raw))
        else:
            print("No private_get_account_accounts() raw helper available in ccxt build.")
    except Exception as e:
        print("raw private endpoint error:", e)
        traceback.print_exc()

    print("\n--- DONE. If all returned balances are empty or error says permissions, check API keys in exchange dashboard. ---")
    print("If you see valid balances in the Bitget app but this script sees 0 or permission errors, you must:")
    print("  • Ensure API key is for FUTURES (USDT-M) and FUTURES read/write or read only for testing.")
    print("  • Ensure 'IP whitelist' is empty or includes your server IP (Render dyno IPs change — better to leave empty during testing).")
    print("  • Ensure passphrase matches exactly and no extra whitespace.")
    print("\nExit.")

if __name__ == "__main__":
    main()
