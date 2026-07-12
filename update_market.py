import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


BRS_URL = "https://brsapi.ir/Api/Market/Gold_Currency.php"

BTC_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin"
    "&vs_currencies=usd"
    "&include_24hr_change=true"
)


def get_market():

    try:

        r = requests.get(
            BRS_URL,
            timeout=20
        )

        data = r.json()

        usd = 0
        gold18 = 0

        for item in data:

            name = str(
                item.get("name", "")
            )

            if "دلار" in name and usd == 0:
                usd = int(item["price"])

            if (
                "طلای 18" in name
                or
                "طلای ۱۸" in name
            ):
                gold18 = int(item["price"])

        return usd, gold18

    except Exception as e:

        print("MARKET ERROR:", e)

        return None, None


def get_bitcoin():

    try:

        r = requests.get(
            BTC_URL,
            timeout=20
        )

        data = r.json()

        price = int(
            data["bitcoin"]["usd"]
        )

        change = round(
            data["bitcoin"]["usd_24h_change"],
            2
        )

        return price, change

    except Exception as e:

        print("BTC ERROR:", e)

        return 0, 0


def main():

    usd, gold18 = get_market()

    if usd is None:
        return

    btc, btc_change = get_bitcoin()

    old_usd = usd
    old_gold = gold18

    try:

        with open(
            "market.json",
            "r",
            encoding="utf-8"
        ) as f:

            old = json.load(f)

        old_usd = old.get(
            "iran",
            {}
        ).get(
            "usd",
            usd
        )

        old_gold = old.get(
            "iran",
            {}
        ).get(
            "gold18",
            gold18
        )

    except Exception:
        pass

    usd_change = usd - old_usd
    gold18_change = gold18 - old_gold

    now = datetime.now(
        ZoneInfo("Asia/Tehran")
    )

    output = {

        "iran": {

            "usd": usd,
            "usd_change": usd_change,

            "gold18": gold18,
            "gold18_change": gold18_change
        },

        "crypto": {

            "btc": btc,
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
