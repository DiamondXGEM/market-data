import requests
import json
import os
import base64
from datetime import datetime


# ===============================
# API KEYS
# ===============================

BRS_API_KEY = os.getenv("BhDCtRpVCPifhVaWtXMSeuBWBuEQxLHu")

if not BRS_API_KEY:
    raise RuntimeError("BRS_API_KEY not found")


GITHUB_TOKEN = os.getenv("Yalda")

if not GITHUB_TOKEN:
    raise RuntimeError("GitHub token 'Yalda' not found")


print("GitHub Token: OK")

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
# BRS MARKET (USD + GOLD)
# ===============================

def get_brs_market():

    url = "https://brsapi.ir/Api/Market/Gold_Currency.php"

    old = load_old()

    try:

        r = requests.get(
            url,
            params={
                "key": BRS_API_KEY
            },
            headers=HEADERS,
            timeout=(10, 30)
        )

        r.raise_for_status()

        data = r.json()


        usd = next(
            item
            for item in data["currency"]
            if item["symbol"] == "USD"
        )


        gold = next(
            item
            for item in data["gold"]
            if item["symbol"] == "IR_GOLD_18K"
        )


        return {
            "usd": int(
                usd["price"]
            ),

            "gold": gold
        }


    except Exception as e:

        print("BRS ERROR:", e)


        return {

            "usd": old.get(
                "iran",
                {}
            ).get(
                "usd",
                0
            ),


            "gold": {

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
        }

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

            print("BTC rate limited")

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

        print("BTC ERROR:", e)


        return load_old().get(
            "crypto",
            {}
        ).get(
            "btc",
            0
        )
        
# ===============================
# USDT
# ===============================

def get_usdt(usd):

    # قیمت تتر در بازار ایران
    # تقریباً برابر دلار آزاد در نظر گرفته می‌شود

    return usd
    
# ===============================
# CHANGE
# ===============================

def calc_change(new, old):

    if old is None:
        return 0

    return new - old

# ===============================
# GITHUB UPDATE
# ===============================

def push_github():

    url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_REPO}/contents/"
        f"{GITHUB_FILE}"
    )


    headers = {

        "Authorization": f"Bearer {GITHUB_TOKEN}",

        "Accept": "application/vnd.github+json"

    }


    old_file = requests.get(
        url,
        headers=headers,
        timeout=20
    )


    if old_file.status_code not in (200, 404):

        print(
            "GitHub GET ERROR:",
            old_file.status_code
        )

        print(
            old_file.text
        )

        return



    sha = None


    if old_file.status_code == 200:

        sha = old_file.json()["sha"]



    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        content = f.read()



    payload = {

        "message": "Auto market update",

        "content": base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8")

    }



    if sha:

        payload["sha"] = sha



    response = requests.put(

        url,

        headers=headers,

        json=payload,

        timeout=20

    )


    if response.status_code in (200, 201):

        print(
            "GitHub updated successfully"
        )

    else:

        print(
            "GitHub UPDATE ERROR:",
            response.status_code
        )

        print(
            response.text
        )

# ===============================
# MAIN
# ===============================

print(
    "Market update started"
)


old = load_old()


old_iran = old.get(
    "iran",
    {}
)


old_crypto = old.get(
    "crypto",
    {}
)

# ===============================
# BRS
# ===============================

brs = get_brs_market()


usd = brs["usd"]


gold = brs["gold"]


gold_price = int(
    gold["price"]
)


print(
    "USD:",
    usd
)


print(
    "GOLD:",
    gold_price
)

# ===============================
# CRYPTO
# ===============================

btc = get_btc()


print(
    "BTC:",
    btc
)



usdt = get_usdt(
    usd
)


print(
    "USDT:",
    usdt
)

# ===============================
# CREATE MARKET JSON
# ===============================

market = {


    "iran": {


        "usd": usd,


        "usd_change": calc_change(

            usd,

            old_iran.get(
                "usd"
            )

        ),



        "gold18": gold_price,


        "gold18_change": calc_change(

            gold_price,

            old_iran.get(
                "gold18"
            )

        ),



        "gold18_percent": gold.get(

            "change_percent",

            0

        )

    },



    "crypto": {


        "btc": btc,


        "btc_change": calc_change(

            btc,

            old_crypto.get(
                "btc"
            )

        ),



        "usdt": usdt,


        "usdt_change": calc_change(

            usdt,

            old_crypto.get(
                "usdt"

            )

        )

    },



    "gold_update": {


        "date": gold.get(

            "date",

            ""

        ),


        "time": gold.get(

            "time",

            ""

        )

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
    "JSON saved successfully"
)

# ===============================
# GITHUB
# ===============================

push_github()



print(
    "Market update completed"
)
