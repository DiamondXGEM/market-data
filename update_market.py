import requests
import json
import os
import subprocess
from datetime import datetime


# ===============================
# API KEYS
# ===============================

EXCHANGE_API_KEY = os.getenv(
    "EXCHANGE_API_KEY",
    "70907a9ff24bb63da4640a3a"
)

BRS_API_KEY = os.getenv(
    "BRS_API_KEY",
    "BhDCtRpVCPifhVaWtXMSeuBWBuEQxLHu"
)


GITHUB_TOKEN = os.getenv(
    "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"
)


DATA_FILE = "market_data.json"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    ),
    "Accept": "application/json"
}



# ===============================
# LOAD OLD JSON
# ===============================

def load_old():

    if os.path.exists(DATA_FILE):

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    return {}



# ===============================
# USD
# ===============================

def get_usd():

    url = (
        f"https://v6.exchangerate-api.com/v6/"
        f"{EXCHANGE_API_KEY}/latest/USD"
    )

    r = requests.get(
        url,
        timeout=20
    )

    r.raise_for_status()

    data = r.json()

    return int(
        data["conversion_rates"]["IRR"] / 10
    )



# ===============================
# BTC
# ===============================

def get_btc():

    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd"
    )


    try:

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )


        if r.status_code == 429:

            print("BTC limited")

            old = load_old()

            return old.get(
                "crypto",
                {}
            ).get(
                "btc",
                0
            )


        r.raise_for_status()


        return int(
            r.json()["bitcoin"]["usd"]
        )


    except Exception as e:

        print(
            "BTC ERROR:",
            e
        )

        old = load_old()

        return old.get(
            "crypto",
            {}
        ).get(
            "btc",
            0
        )



# ===============================
# GOLD
# ===============================

def get_gold():

    url = (
        "https://brsapi.ir/Api/Market/Gold_Currency.php"
    )


    r = requests.get(
        url,
        params={
            "key": BRS_API_KEY
        },
        headers=HEADERS,
        timeout=20
    )


    r.raise_for_status()


    data = r.json()


    gold = next(
        x for x in data["gold"]
        if x["symbol"] == "IR_GOLD_18K"
    )


    return gold



# ===============================
# CHANGE
# ===============================

def calc_change(
    new,
    old
):

    if old is None:
        return 0

    return new - old



# ===============================
# PUSH TO GITHUB
# ===============================

def push_github():

    if not GITHUB_TOKEN:

        print(
            "No GitHub token"
        )

        return


    subprocess.run(
        [
            "git",
            "config",
            "user.name",
            "market-bot"
        ]
    )


    subprocess.run(
        [
            "git",
            "config",
            "user.email",
            "bot@market.local"
        ]
    )


    subprocess.run(
        [
            "git",
            "add",
            DATA_FILE
        ]
    )


    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "Auto market update"
        ]
    )


    subprocess.run(
        [
            "git",
            "push",
            f"https://{GITHUB_TOKEN}@github.com/diamondxgem/market.git",
            "main"
        ]
    )


    print(
        "GitHub updated"
    )



# ===============================
# MAIN
# ===============================

print(
    "Market update started"
)


old = load_old()



usd = get_usd()

print(
    "USD:",
    usd
)



btc = get_btc()

print(
    "BTC:",
    btc
)



gold = get_gold()

print(
    "GOLD:",
    gold["price"]
)



old_iran = old.get(
    "iran",
    {}
)


old_crypto = old.get(
    "crypto",
    {}
)



market = {

    "iran": {

        "usd": usd,

        "usd_change": calc_change(
            usd,
            old_iran.get("usd")
        ),


        "gold18": gold["price"],

        "gold18_change": calc_change(
            gold["price"],
            old_iran.get("gold18")
        ),

        "gold18_percent":
            gold["change_percent"]

    },


    "crypto": {

        "btc": btc,

        "btc_change": calc_change(
            btc,
            old_crypto.get("btc")
        )

    },


    "gold_update": {

        "date": gold["date"],

        "time": gold["time"]

    },


    "updated":
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

}



with open(
    DATA_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        market,
        f,
        ensure_ascii=False,
        indent=4
    )


print(
    "JSON saved"
)


push_github()
