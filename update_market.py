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


# GitHub token from Railway Variables
GITHUB_TOKEN = os.getenv(
    "Yalda"
)


print(
    "Yalda EXISTS:",
    bool(GITHUB_TOKEN)
)



# ===============================
# SETTINGS
# ===============================

DATA_FILE = "market.json"


GITHUB_REPO = "DiamondXGEM/market-data"


GITHUB_FILE = "market.json"



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

    try:

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


    except Exception as e:

        print(
            "USD ERROR:",
            e
        )

        return load_old().get(
            "iran",
            {}
        ).get(
            "usd",
            0
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

            return load_old().get(
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


        return load_old().get(
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


    try:

        r = requests.get(
            url,
            params={
                "key": BRS_API_KEY
            },
            headers=HEADERS,
            timeout=(10,30)
        )


        r.raise_for_status()


        data = r.json()


        return next(
            item
            for item in data["gold"]
            if item["symbol"] == "IR_GOLD_18K"
        )


    except Exception as e:

        print(
            "GOLD ERROR:",
            e
        )


        old = load_old()


        return {

            "price": old.get(
                "iran",
                {}
            ).get(
                "gold18",
                0
            ),

            "change_percent": 0,

            "date": "",

            "time": ""

        }



# ===============================
# CHANGE
# ===============================

def calc_change(new, old):

    if old is None:

        return 0

    return new - old

# ===============================
# GITHUB API UPDATE
# ===============================

def push_github():

    if not GITHUB_TOKEN:

        print(
            "No GitHub token"
        )

        return


    url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_REPO}/contents/"
        f"{GITHUB_FILE}"
    )


    headers = {

        "Authorization":
            f"Bearer {GITHUB_TOKEN}",

        "Accept":
            "application/vnd.github+json"

    }



    old_file = requests.get(
        url,
        headers=headers,
        timeout=20
    )


    sha = None


    if old_file.status_code == 200:

        sha = old_file.json()["sha"]



    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        content = f.read()



    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")



    payload = {

        "message":
            "Auto market update",

        "content":
            encoded

    }



    if sha:

        payload["sha"] = sha



    response = requests.put(
        url,
        headers=headers,
        json=payload,
        timeout=20
    )



    if response.status_code in [200, 201]:

        print(
            "GitHub updated successfully"
        )


    else:

        print(
            "GitHub ERROR:",
            response.text
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

        "usd":
            usd,


        "usd_change":
            calc_change(
                usd,
                old_iran.get("usd")
            ),


        "gold18":
            gold["price"],


        "gold18_change":
            calc_change(
                gold["price"],
                old_iran.get("gold18")
            ),


        "gold18_percent":
            gold.get(
                "change_percent",
                0
            )

    },


    "crypto": {

        "btc":
            btc,


        "btc_change":
            calc_change(
                btc,
                old_crypto.get("btc")
            )

    },


    "gold_update": {

        "date":
            gold.get(
                "date",
                ""
            ),


        "time":
            gold.get(
                "time",
                ""
            )

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
