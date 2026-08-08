import requests
import json
import os
import base64
from datetime import datetime


# ============================================================
# API KEYS
# ============================================================

BRS_API_KEY = os.getenv("BRS_API_KEY")

if not BRS_API_KEY:
    raise RuntimeError("BRS_API_KEY not found")

GITHUB_TOKEN = os.getenv("Yalda")

if not GITHUB_TOKEN:
    raise RuntimeError("GitHub token 'Yalda' not found")

print("GitHub Token: OK")
print("BRS API Key: OK")


# ============================================================
# SETTINGS
# ============================================================

DATA_FILE = "market.json"

GITHUB_REPO = "DiamondXGEM/market-data"
GITHUB_FILE = "market.json"

BRS_URL = "https://api.brsapi.ir/Market/Gold_Currency.php"

BTC_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin&vs_currencies=usd"
)


# ============================================================
# HEADERS
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    ),
    "Accept": "application/json",
}


# ============================================================
# LOAD OLD DATA
# ============================================================

def load_old():

    if not os.path.exists(DATA_FILE):
        return {}

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            if isinstance(data, dict):
                return data

    except Exception as e:

        print("OLD DATA ERROR:", repr(e))

    return {}


# ============================================================
# SAFE INTEGER
# ============================================================

def safe_int(value, default=0):

    if value is None:
        return default

    if isinstance(value, bool):
        return default

    try:

        if isinstance(value, float):
            return int(value)

        text = str(value).strip()

        if not text:
            return default

        # حذف جداکننده‌های معمول
        text = (
            text
            .replace(",", "")
            .replace("٬", "")
            .replace(" ", "")
        )

        return int(float(text))

    except Exception:

        return default


# ============================================================
# FIND ITEM BY SYMBOL
# ============================================================

def find_symbol(items, symbols):

    if not isinstance(items, list):
        return None

    if isinstance(symbols, str):
        symbols = [symbols]

    wanted = {
        str(x).strip().upper()
        for x in symbols
    }

    for item in items:

        if not isinstance(item, dict):
            continue

        symbol = item.get("symbol")

        if symbol is None:
            continue

        if str(symbol).strip().upper() in wanted:
            return item

    return None


# ============================================================
# DEBUG BRS RESPONSE
# ============================================================

def print_brs_response(data):

    print("")
    print("=" * 60)
    print("BRS RAW RESPONSE")
    print("=" * 60)

    try:

        print(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=4
            )
        )

    except Exception:

        print(repr(data))

    print("=" * 60)
    print("")


# ============================================================
# BRS MARKET
# USD + USDT + GOLD
# ============================================================

def get_brs_market():

    old = load_old()

    old_usd = (
        old
        .get("iran", {})
        .get("usd", 0)
    )

    old_usdt = (
        old
        .get("crypto", {})
        .get("usdt", 0)
    )

    old_gold = (
        old
        .get("iran", {})
        .get("gold18", 0)
    )

    try:

        print("")
        print("Connecting to BRS...")
        print("BRS URL:", BRS_URL)

        response = requests.get(
            BRS_URL,
            params={
                "key": BRS_API_KEY
            },
            headers=HEADERS,
            timeout=(20, 60)
        )

        print(
            "BRS STATUS:",
            response.status_code
        )

        print(
            "BRS CONTENT TYPE:",
            response.headers.get(
                "Content-Type",
                ""
            )
        )

        response.raise_for_status()

        # ----------------------------------------------------
        # JSON PARSE
        # ----------------------------------------------------

        try:

            data = response.json()

        except Exception as e:

            print(
                "BRS JSON PARSE ERROR:",
                repr(e)
            )

            print(
                "BRS TEXT RESPONSE:",
                response.text[:5000]
            )

            raise Exception(
                "BRS returned invalid JSON"
            )

        # ----------------------------------------------------
        # SHOW RAW RESPONSE
        # ----------------------------------------------------

        print_brs_response(data)

        if not isinstance(data, dict):

            raise Exception(
                "BRS response is not a JSON object"
            )

        # ----------------------------------------------------
        # POSSIBLE DATA LOCATIONS
        # ----------------------------------------------------

        # حالت معمول
        currency = data.get(
            "currency",
            []
        )

        gold_list = data.get(
            "gold",
            []
        )

        # بعضی APIها اطلاعات را داخل data می‌گذارند
        if (
            not isinstance(currency, list)
            and isinstance(
                data.get("data"),
                dict
            )
        ):

            nested = data["data"]

            currency = nested.get(
                "currency",
                []
            )

            gold_list = nested.get(
                "gold",
                []
            )

        # ----------------------------------------------------
        # DEBUG
        # ----------------------------------------------------

        print(
            "BRS currency items:",
            len(currency)
            if isinstance(currency, list)
            else "NOT LIST"
        )

        print(
            "BRS gold items:",
            len(gold_list)
            if isinstance(gold_list, list)
            else "NOT LIST"
        )

        # ----------------------------------------------------
        # FIND USD
        # ----------------------------------------------------

        usd = find_symbol(
            currency,
            [
                "USD",
                "USD_TMN",
                "USD_IRR"
            ]
        )

        # ----------------------------------------------------
        # FIND USDT
        # ----------------------------------------------------

        usdt = find_symbol(
            currency,
            [
                "USDT",
                "USDT_TMN",
                "USDT_IRR"
            ]
        )

        # ----------------------------------------------------
        # FIND GOLD
        # ----------------------------------------------------

        gold = find_symbol(
            gold_list,
            [
                "IR_GOLD_18K",
                "GOLD_18K",
                "GOLD18",
                "18K"
            ]
        )

        # ----------------------------------------------------
        # PRINT FOUND ITEMS
        # ----------------------------------------------------

        print("")
        print("BRS USD ITEM:")
        print(
            json.dumps(
                usd,
                ensure_ascii=False,
                indent=4
            )
            if usd
            else "NOT FOUND"
        )

        print("")
        print("BRS USDT ITEM:")
        print(
            json.dumps(
                usdt,
                ensure_ascii=False,
                indent=4
            )
            if usdt
            else "NOT FOUND"
        )

        print("")
        print("BRS GOLD ITEM:")
        print(
            json.dumps(
                gold,
                ensure_ascii=False,
                indent=4
            )
            if gold
            else "NOT FOUND"
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not usd:

            print(
                "WARNING: USD symbol not found"
            )

        if not usdt:

            print(
                "WARNING: USDT symbol not found"
            )

        if not gold:

            print(
                "WARNING: GOLD symbol not found"
            )

        # ----------------------------------------------------
        # USD
        # ----------------------------------------------------

        if usd:

            usd_price = safe_int(
                usd.get("price"),
                0
            )

        else:

            usd_price = old_usd

        # ----------------------------------------------------
        # USDT
        # ----------------------------------------------------

        if usdt:

            usdt_price = safe_int(
                usdt.get("price"),
                0
            )

        else:

            usdt_price = old_usdt

        # ----------------------------------------------------
        # GOLD
        # ----------------------------------------------------

        if gold:

            gold_price = safe_int(
                gold.get("price"),
                0
            )

            gold_change = gold.get(
                "change_percent",
                0
            )

            gold_date = gold.get(
                "date",
                ""
            )

            gold_time = gold.get(
                "time",
                ""
            )

        else:

            gold_price = old_gold
            gold_change = 0
            gold_date = ""
            gold_time = ""

        # ----------------------------------------------------
        # CHECK VALID VALUES
        # ----------------------------------------------------

        if usd_price <= 0:

            print(
                "WARNING: Invalid USD price. "
                "Using old value."
            )

            usd_price = old_usd

        if usdt_price <= 0:

            print(
                "WARNING: Invalid USDT price. "
                "Using old value."
            )

            usdt_price = old_usdt

        if gold_price <= 0:

            print(
                "WARNING: Invalid GOLD price. "
                "Using old value."
            )

            gold_price = old_gold

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print("")
        print("BRS FINAL VALUES")
        print("----------------")
        print("USD :", usd_price)
        print("USDT:", usdt_price)
        print("GOLD:", gold_price)
        print("")

        return {

            "usd": usd_price,

            "usdt": usdt_price,

            "gold": {

                "price": gold_price,

                "change_percent": gold_change,

                "date": gold_date,

                "time": gold_time

            }

        }

    except Exception as e:

        print("")
        print("=" * 60)
        print("BRS ERROR")
        print("=" * 60)
        print(repr(e))
        print("=" * 60)
        print("")

        print(
            "Using previous BRS values..."
        )

        return {

            "usd": old_usd,

            "usdt": old_usdt,

            "gold": {

                "price": old_gold,

                "change_percent": 0,

                "date": "",

                "time": ""

            }

        }


# ============================================================
# BTC
# ============================================================

def get_btc():

    old = load_old()

    old_btc = (
        old
        .get("crypto", {})
        .get("btc", 0)
    )

    try:

        print("Connecting to CoinGecko...")

        response = requests.get(
            BTC_URL,
            headers=HEADERS,
            timeout=20
        )

        print(
            "BTC STATUS:",
            response.status_code
        )

        if response.status_code == 429:

            print(
                "BTC rate limited"
            )

            return old_btc

        response.raise_for_status()

        data = response.json()

        btc = safe_int(
            data
            .get("bitcoin", {})
            .get("usd"),
            0
        )

        if btc <= 0:

            print(
                "BTC invalid response"
            )

            return old_btc

        return btc

    except Exception as e:

        print(
            "BTC ERROR:",
            repr(e)
        )

        return old_btc


# ============================================================
# CHANGE
# ============================================================

def calc_change(new, old):

    if old is None:
        return 0

    try:

        return new - old

    except Exception:

        return 0


# ============================================================
# GITHUB UPDATE
# ============================================================

def push_github():

    url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_REPO}/contents/"
        f"{GITHUB_FILE}"
    )

    headers = {

        "Authorization":
            f"Bearer {GITHUB_TOKEN}",

        "Accept":
            "application/vnd.github+json",

        "X-GitHub-Api-Version":
            "2022-11-28"

    }

    try:

        print("")
        print("Connecting to GitHub...")

        old_file = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        print(
            "GitHub GET STATUS:",
            old_file.status_code
        )

        if old_file.status_code not in (
            200,
            404
        ):

            print(
                "GitHub GET ERROR:",
                old_file.status_code
            )

            print(
                old_file.text
            )

            return False

        sha = None

        if old_file.status_code == 200:

            try:

                sha = old_file.json()["sha"]

            except Exception as e:

                print(
                    "GitHub SHA ERROR:",
                    repr(e)
                )

                return False

        # ----------------------------------------------------
        # READ MARKET.JSON
        # ----------------------------------------------------

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read()

        # ----------------------------------------------------
        # PAYLOAD
        # ----------------------------------------------------

        payload = {

            "message":
                "Auto market update",

            "content":
                base64.b64encode(
                    content.encode("utf-8")
                ).decode("utf-8")

        }

        if sha:

            payload["sha"] = sha

        # ----------------------------------------------------
        # PUSH
        # ----------------------------------------------------

        response = requests.put(
            url,
            headers=headers,
            json=payload,
            timeout=20
        )

        print(
            "GitHub PUT STATUS:",
            response.status_code
        )

        if response.status_code in (
            200,
            201
        ):

            print(
                "GitHub updated successfully"
            )

            return True

        print(
            "GitHub UPDATE ERROR:",
            response.status_code
        )

        print(
            response.text
        )

        return False

    except Exception as e:

        print(
            "GitHub ERROR:",
            repr(e)
        )

        return False


# ============================================================
# MAIN
# ============================================================

print("")
print("=" * 60)
print("MARKET UPDATE STARTED")
print("=" * 60)
print("")


# ============================================================
# OLD DATA
# ============================================================

old = load_old()

old_iran = old.get(
    "iran",
    {}
)

old_crypto = old.get(
    "crypto",
    {}
)


# ============================================================
# BRS
# ============================================================

brs = get_brs_market()

usd = brs["usd"]

usdt = brs["usdt"]

gold = brs["gold"]

gold_price = safe_int(
    gold.get("price"),
    0
)


print("")
print("FINAL USD :", usd)
print("FINAL USDT:", usdt)
print("FINAL GOLD:", gold_price)


# ============================================================
# BTC
# ============================================================

btc = get_btc()

print(
    "FINAL BTC :",
    btc
)


# ============================================================
# CREATE MARKET JSON
# ============================================================

market = {

    "iran": {

        "usd": usd,

        "usd_change": calc_change(
            usd,
            old_iran.get("usd")
        ),

        "gold18": gold_price,

        "gold18_change": calc_change(
            gold_price,
            old_iran.get("gold18")
        ),

        "gold18_percent":
            gold.get(
                "change_percent",
                0
            )

    },

    "crypto": {

        "btc": btc,

        "btc_change": calc_change(
            btc,
            old_crypto.get("btc")
        ),

        "usdt": usdt,

        "usdt_change": calc_change(
            usdt,
            old_crypto.get("usdt")
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


# ============================================================
# PRINT FINAL JSON
# ============================================================

print("")
print("=" * 60)
print("FINAL MARKET JSON")
print("=" * 60)

print(
    json.dumps(
        market,
        ensure_ascii=False,
        indent=4
    )
)

print("=" * 60)


# ============================================================
# SAVE JSON
# ============================================================

try:

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

except Exception as e:

    print(
        "JSON SAVE ERROR:",
        repr(e)
    )

    raise


# ============================================================
# GITHUB
# ============================================================

github_ok = push_github()


# ============================================================
# FINAL STATUS
# ============================================================

print("")
print("=" * 60)

if github_ok:

    print(
        "MARKET UPDATE COMPLETED SUCCESSFULLY"
    )

else:

    print(
        "MARKET DATA SAVED LOCALLY"
    )

    print(
        "BUT GITHUB UPDATE FAILED"
    )

print("=" * 60)


