import requests

API_KEY = "70907a9ff24bb63da4640a3a"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json"
}

print("===== USD =====")

usd = requests.get(
    f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD",
    timeout=20
)

print(usd.status_code)
print(usd.text[:500])


print("\n===== BTC =====")

btc = requests.get(
    "https://api.coingecko.com/api/v3/coins/bitcoin",
    headers=headers,
    timeout=20
)

print(btc.status_code)
print(btc.text[:500])


print("\n===== GOLD =====")

gold = requests.get(
    "https://brsapi.ir/Api/Market/Gold_Currency.php",
    headers=headers,
    timeout=20
)

print(gold.status_code)
print(gold.text[:500])
