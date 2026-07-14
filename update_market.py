import requests
import json
import os
import base64


# ===============================
# API KEYS
# ===============================

EXCHANGE_API_KEY = "70907a9ff24bb63da4640a3a"
BRS_API_KEY = "BhDCtRpVCPifhVaWtXMSeuBWBuEQxLHu"


# ===============================
# GITHUB SETTINGS
# ===============================

GITHUB_TOKEN = "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"

GITHUB_OWNER = "DiamondXGEM"
GITHUB_REPO = "market-data"

GITHUB_FILE = "market.json"


# ===============================
# FILE SETTINGS
# ===============================

DATA_FILE = "market.json"


headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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
# SAVE LOCAL FILE
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

    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        if r.status_code == 429:
            print("BTC API محدود شده، مقدار قبلی استفاده می‌شود")

            old = load_old()

            return old.get(
                "btc",
                0
            )

        r.raise_for_status()

        return int(
            r.json()["bitcoin"]["usd"]
        )

    except Exception as e:

        print("BTC Error:", e)

        old = load_old()

        return old.get(
            "btc",
            0
        )
print("BTC done")


# ===============================
# GOLD
# ===============================
print("Getting GOLD...")
gold = get_gold()
print("GOLD done:", gold)
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


    return gold["price"]



# ===============================
# CHANGE
# ===============================

def calc_change(current, old):

    if old is None:
        return 0

    return current - old



# ===============================
# GITHUB UPDATE
# ===============================
print("Saving JSON...")
def update_github(file_content):

    url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    )


    gh_headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }


    # گرفتن SHA فایل قبلی

    r = requests.get(
        url,
        headers=gh_headers
    )


    sha = None

    if r.status_code == 200:

        sha = r.json()["sha"]



    content = base64.b64encode(
        file_content.encode("utf-8")
    ).decode()



    payload = {

        "message": "Update market data",

        "content": content

    }


    if sha:
        payload["sha"] = sha



    r = requests.put(
        url,
        headers=gh_headers,
        json=payload
    )


    r.raise_for_status()

    print("✅ GitHub market.json updated")



# ===============================
# MAIN
# ===============================

print("🚀 Market update started")


old = load_old()


usd = get_usd()
print("USD:", usd)


btc = get_btc()
print("BTC:", btc)


gold = get_gold()
print("GOLD:", gold)



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
        "price": gold,
        "change": calc_change(
            gold,
            old.get("gold")
        )
    }

}



save_data(market)



with open(
    DATA_FILE,
    "r",
    encoding="utf-8"
) as f:

    github_content = f.read()



update_github(
    github_content
)



print("✅ DONE")
