import requests
import json
import os


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
        "Chrome/120.0 Safari/537.36"
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
# SAVE DATA
# ===============================

def save_data(data):

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )



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

    # نرخ دلار به تومان
    usd = data["conversion_rates"]["IRR"] / 10

    return round(usd)



# ===============================
# BTC
# ===============================

def get_btc():

    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd"
    )

    r = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    r.raise_for_status()

    return int(
        r.json()["bitcoin"]["usd"]
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
        headers=headers,
        timeout=20
    )

    r.raise_for_status()

    data = r.json()


    gold = next(
        item
        for item in data["gold"]
        if item["symbol"] == "IR_GOLD_18K"
    )


    return {
        "price": gold["price"],
        "change": gold["change_value"]
    }



# ===============================
# CHANGE
# ===============================

def calc_change(
    current,
    old
):

    if old is None:
        return 0

    return current - old



# ===============================
# MAIN
# ===============================

old = load_old()


usd = get_usd()
btc = get_btc()
gold = get_gold()


market = {

    "usd": {
        "price": usd,
        "change": calc_change(
            usd,
            old.get("usd")
        )
    },


    "btc": {
        "price": btc,
        "change": calc_change(
            btc,
            old.get("btc")
        )
    },


    "gold": {
        "price": gold["price"],
        "change": calc_change(
            gold["price"],
            old.get("gold")
        )
    }

}



save_data(
    {
        "usd": usd,
        "btc": btc,
        "gold": gold["price"]
    }
)



# ===============================
# OUTPUT
# ===============================

print(
    json.dumps(
        market,
        ensure_ascii=False,
        indent=2
    )
)
