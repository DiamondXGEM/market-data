import requests
import json
import os
from datetime import datetime


# ===============================
# API KEYS
# ===============================

EXCHANGE_API_KEY = "70907a9ff24bb63da4640a3a"
BRS_API_KEY = "BhDCtRpVCPifhVaWtXMSeuBWBuEQxLHu"


# ===============================
# SETTINGS
# ===============================

DATA_FILE = "market_data.json"


headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    ),
    "Accept": "application/json"
}


# ===============================
# LOAD OLD DATA
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

    # دلار ریال به تومان
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
            headers=headers,
            timeout=20
        )


        if r.status_code == 429:

            print(
                "BTC rate limited"
            )

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
            "BTC error:",
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
# GOLD 18K
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
        headers=headers,
        timeout=20
    )


    r.raise_for_status()


    data = r.json()


    gold18 = next(
        item
        for item in data["gold"]
        if item["symbol"] == "IR_GOLD_18K"
    )


    return {
        "price": gold18["price"],
        "change": gold18["change_value"],
        "percent": gold18["change_percent"],
        "date": gold18["date"],
        "time": gold18["time"]
    }



# ===============================
# CHANGE CALC
# ===============================

def change(new, old):

    if old is None:
        return 0

    return new - old



# ===============================
# MAIN
# ===============================

print("Market update started")


old = load_old()


# USD

usd = get_usd()

print(
    "USD:",
    usd
)



# BTC

btc = get_btc()

print(
    "BTC:",
    btc
)

print("BTC done")


# GOLD

print(
    "Getting GOLD..."
)


gold = get_gold()


print(
    "GOLD:",
    gold["price"]
)



# ===============================
# BUILD JSON
# ===============================

old_usd = old.get(
    "iran",
    {}
).get(
    "usd"
)


old_gold = old.get(
    "iran",
    {}
).get(
    "gold18"
)


old_btc = old.get(
    "crypto",
    {}
).get(
    "btc"
)



market = {

    "iran": {

        "usd": usd,

        "usd_change": change(
            usd,
            old_usd
        ),


        "gold18": gold["price"],

        "gold18_change": change(
            gold["price"],
            old_gold
        ),

        "gold18_percent": gold["percent"]

    },


    "crypto": {

        "btc": btc,

        "btc_change": change(
            btc,
            old_btc
        )

    },


    "gold_update": {

        "date": gold["date"],

        "time": gold["time"]

    },


    "updated": datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

}



# ===============================
# SAVE JSON
# ===============================

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


print(
    json.dumps(
        market,
        ensure_ascii=False,
        indent=4
    )
        )
