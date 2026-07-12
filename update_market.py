import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


API_KEY = os.getenv("70907a9ff24bb63da4640a3a")

URL = (
    f"https://v6.exchangerate-api.com/v6/"
    f"{API_KEY}/latest/USD"
)

BTC_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin"
    "&vs_currencies=usd"
    "&include_24hr_change=true"
)


def get_dollar_price():

    try:

        r = requests.get(URL, timeout=15)
        data = r.json()

        rate = data["conversion_rates"]["IRR"]

        return int(rate / 10)

    except Exception as e:

        print("DOLLAR ERROR:", e)
        return None


def get_bitcoin():

    try:

        r = requests.get(BTC_URL, timeout=20)
        data = r.json()

        price = int(data["bitcoin"]["usd"])

        change = round(
            data["bitcoin"]["usd_24h_change"],
            2
        )

        return price, change

    except Exception as e:

        print("BTC ERROR:", e)

        return 0, 0


def main():

    dollar = get_dollar_price()

    if dollar is None:
        return

    btc_price, btc_change = get_bitcoin()

    now = datetime.now(
        ZoneInfo("Asia/Tehran")
    )

    output = {

        "iran": {

            "usd": dollar,
            "usd_change": 0,

            "gold18": 0,
            "gold18_change": 0
        },

        "crypto": {

            "btc": btc_price,
            "btc_change": btc_change
        },

        "updated": now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    with open(
        "market.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=4
        )

    print("✅ MARKET UPDATED")


if __name__ == "__main__":
    main()
