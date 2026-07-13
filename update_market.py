import json
from datetime import datetime

import requests

API_KEY = "70907a9ff24bb63da4640a3a"

# ======================
# USD (ExchangeRate API)
# ======================

usd = requests.get(
    f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD",
    timeout=20
).json()

usd_price = int(
    usd["conversion_rates"]["IRR"] / 10
)

# ======================
# BTC (CoinGecko)
# ======================

btc = requests.get(
    "https://api.coingecko.com/api/v3/coins/bitcoin",
    timeout=20,
    headers={
        "accept": "application/json",
        "User-Agent": "market-data-bot"
    }
).json()

btc_price = round(
    btc["market_data"]["current_price"]["usd"],
    2
)

btc_change = round(
    btc["market_data"]["price_change_percentage_24h"],
    2
)

# ======================
# GOLD (BRS API)
# ======================

gold = requests.get(
    "https://brsapi.ir/Api/Market/Gold_Currency.php",
    timeout=20
).json()

gold18 = 0
gold_change = 0

for item in gold:
    if item.get("symbol") == "IR_GOLD_18K":
        gold18 = int(item["price"])
        gold_change = float(item.get("change_percent", 0))
        break

# ======================
# SAVE JSON
# ======================

data = {
    "iran": {
        "usd": usd_price,
        "usd_change": 0,
        "gold18": gold18,
        "gold18_change": gold_change
    },
    "crypto": {
        "btc": btc_price,
        "btc_change": btc_change
    },
    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

with open(
    "market.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
    )

print("✅ Market Updated")
