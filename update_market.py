import requests

API_KEY = "70907a9ff24bb63da4640a3a"

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
    timeout=20
)

print(btc.status_code)
print(btc.text[:500])

print("\n===== GOLD =====")

gold = requests.get(
    "https://brsapi.ir/Api/Market/Gold_Currency.php",
    timeout=20
)

print(gold.status_code)
print(gold.text)
