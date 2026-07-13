import json
from datetime import datetime

import requests

API_KEY = "70907a9ff24bb63da4640a3a"

# ======================
# USD
# ======================

usd = requests.get(
    f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD",
    timeout=20
).json()

usd_price = int(
    usd["conversion_rates"]["IRR"] / 10
)

# ======================
# BTC
# ======================

btc = requests.get(
    "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT",
    timeout=20
).json()

btc_price = round(
    float(btc["lastPrice"]),
    2
)

btc_change = round(
    float(btc["priceChangePercent"]),
    2
)

# ======================
# GOLD
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
# SAVE
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

print("Market Updated ✔")
