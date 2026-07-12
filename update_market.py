import os
import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo


API_KEY = os.getenv("EXCHANGE_API_KEY")

URL = (
    f"https://v6.exchangerate-api.com/v6/"
    f"{API_KEY}/latest/USD"
)


def get_dollar_price():

    try:
        r = requests.get(URL, timeout=15)
        data = r.json()

        rate = data["conversion_rates"]["IRR"]

        # ریال به تومان
        toman = int(rate / 10)

        return toman

    except Exception as e:
        print("DOLLAR ERROR:", e)
        return None



def main():

    dollar = get_dollar_price()

    if not dollar:
        return

    now = datetime.now(
        ZoneInfo("Asia/Tehran")
    )

    output = {
        "usd": dollar,
        "gold18": 0,
        "time": now.strftime("%H:%M"),
        "date": now.strftime("%Y-%m-%d")
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
