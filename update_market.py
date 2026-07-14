import requests
import json
import os
import base64
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

print(
    "TOKEN EXISTS:",
    bool(GITHUB_TOKEN)
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

    return next(
        x for x in data["gold"]
        if x["symbol"] == "IR_GOLD_18K"
    )



# ===============================
# CHANGE
# ===============================

def calc_change(new, old):

    if old is None:
        return 0

    return new - old
