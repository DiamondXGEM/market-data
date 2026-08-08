import requests
import json
import os
import base64
import time
from datetime import datetime


# ============================================================
# API KEYS
# ============================================================

NAVASAN_API_KEY = os.getenv("NAVASAN_API_KEY")
BRS_API_KEY = os.getenv("BRS_API_KEY")
GITHUB_TOKEN = os.getenv("Yalda")


if not NAVASAN_API_KEY:
    raise RuntimeError(
        "NAVASAN_API_KEY not found"
    )

if not GITHUB_TOKEN:
    raise RuntimeError(
        "GitHub token 'Yalda' not found"
    )


print("Navasan API Key: OK")
print(
    "BRS API Key:",
    "OK" if BRS_API_KEY else "NOT SET - BRS backup disabled"
)
print("GitHub Token: OK")


# ============================================================
# SETTINGS
# ============================================================

DATA_FILE = "market.json"

GITHUB_REPO = "DiamondXGEM/market-data"
GITHUB_FILE = "market.json"


# ------------------------------------------------------------
# NAVASAN
# طبق مستندات رسمی Navasan
# ------------------------------------------------------------

NAVASAN_URL = (
    "http://api.navasan.tech/latest/"
)


# ------------------------------------------------------------
# BRS BACKUP
# ------------------------------------------------------------

BRS_URL = (
    "https://api.brsapi.ir/"
    "Market/Gold_Currency.php"
)


# ------------------------------------------------------------
# COINGECKO BACKUP
# ------------------------------------------------------------

BTC_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin&vs_currencies=usd"
)


# ============================================================
# RETRY SETTINGS
# ============================================================

MAX_RETRIES = 3

RETRY_DELAY = 3


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

    "Accept": "application/json"

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

        print(
            "OLD DATA ERROR:",
            repr(e)
        )

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
# SAFE FLOAT
# ============================================================

def safe_float(value, default=0):

    if value is None:
        return default

    try:

        text = str(value).strip()

        if not text:
            return default

        text = (
            text
            .replace(",", "")
            .replace("٬", "")
            .replace(" ", "")
        )

        return float(text)

    except Exception:

        return default


# ============================================================
# CALCULATE PERCENT
# ============================================================

def calculate_percent(
    value,
    change
):

    value = safe_float(
        value,
        0
    )

    change = safe_float(
        change,
        0
    )

    if value <= 0:
        return 0

    previous = value - change

    if previous <= 0:
        return 0

    try:

        percent = (
            change / previous
        ) * 100

        return round(
            percent,
            2
        )

    except Exception:

        return 0


# ============================================================
# FIND BRS SYMBOL
# ============================================================

def find_symbol(
    items,
    symbols
):

    if not isinstance(
        items,
        list
    ):
        return None

    if isinstance(
        symbols,
        str
    ):
        symbols = [
            symbols
        ]

    wanted = {
        str(x)
        .strip()
        .upper()
        for x in symbols
    }

    for item in items:

        if not isinstance(
            item,
            dict
        ):
            continue

        symbol = item.get(
            "symbol"
        )

        if symbol is None:
            continue

        if (
            str(symbol)
            .strip()
            .upper()
            in wanted
        ):

            return item

    return None


# ============================================================
# NAVASAN REQUEST
# ============================================================

def request_navasan():

    print("")
    print(
        "Connecting to Navasan..."
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"Navasan attempt "
                f"{attempt}/{MAX_RETRIES}"
            )

            response = requests.get(

                NAVASAN_URL,

                params={
                    "api_key":
                        NAVASAN_API_KEY
                },

                headers=HEADERS,

                timeout=(
                    10,
                    30
                )
            )

            print(
                "NAVASAN STATUS:",
                response.status_code
            )

            print(
                "NAVASAN CONTENT TYPE:",
                response.headers.get(
                    "Content-Type",
                    ""
                )
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(
                data,
                dict
            ):

                raise Exception(
                    "Navasan response is not JSON object"
                )

            return data

        except requests.exceptions.Timeout as e:

            print(
                "NAVASAN TIMEOUT:",
                repr(e)
            )

        except requests.exceptions.ConnectionError as e:

            print(
                "NAVASAN CONNECTION ERROR:",
                repr(e)
            )

        except requests.exceptions.RequestException as e:

            print(
                "NAVASAN REQUEST ERROR:",
                repr(e)
            )

            # خطاهای 401/429/503 معمولاً با Retry
            # در دفعات بعد هم ارزش امتحان دارند.

        except Exception as e:

            print(
                "NAVASAN ERROR:",
                repr(e)
            )

        if attempt < MAX_RETRIES:

            print(
                f"Retrying Navasan "
                f"in {RETRY_DELAY} seconds..."
            )

            time.sleep(
                RETRY_DELAY
            )

    return None


# ============================================================
# NAVASAN MARKET
# USD + GOLD + BTC
# ============================================================

def get_navasan_market():

    old = load_old()

    old_usd = safe_int(
        old
        .get("iran", {})
        .get("usd", 0)
    )

    old_gold = safe_int(
        old
        .get("iran", {})
        .get("gold18", 0)
    )

    old_btc = safe_int(
        old
        .get("crypto", {})
        .get("btc", 0)
    )

    try:

        data = request_navasan()

        if data is None:

            raise Exception(
                "Navasan unavailable"
            )

        print("")
        print(
            "=" * 60
        )

        print(
            "NAVASAN RAW RESPONSE"
        )

        print(
            "=" * 60
        )

        print(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=4
            )
        )

        print(
            "=" * 60
        )

        # ----------------------------------------------------
        # USD
        # ----------------------------------------------------

        usd_data = data.get(
            "usd_sell"
        )

        if isinstance(
            usd_data,
            dict
        ):

            usd = safe_int(
                usd_data.get(
                    "value"
                ),
                0
            )

            usd_change = safe_int(
                usd_data.get(
                    "change"
                ),
                0
            )

            usd_date = usd_data.get(
                "date",
                ""
            )

        else:

            usd = 0
            usd_change = 0
            usd_date = ""

        # ----------------------------------------------------
        # GOLD 18K
        # ----------------------------------------------------

        gold_data = data.get(
            "18ayar"
        )

        if isinstance(
            gold_data,
            dict
        ):

            gold = safe_int(
                gold_data.get(
                    "value"
                ),
                0
            )

            gold_change = safe_int(
                gold_data.get(
                    "change"
                ),
                0
            )

            gold_date = gold_data.get(
                "date",
                ""
            )

        else:

            gold = 0
            gold_change = 0
            gold_date = ""

        # ----------------------------------------------------
        # BTC
        # ----------------------------------------------------

        btc_data = data.get(
            "btc"
        )

        if isinstance(
            btc_data,
            dict
        ):

            btc = safe_int(
                btc_data.get(
                    "value"
                ),
                0
            )

            btc_change = safe_int(
                btc_data.get(
                    "change"
                ),
                0
            )

            btc_date = btc_data.get(
                "date",
                ""
            )

        else:

            btc = 0
            btc_change = 0
            btc_date = ""

        # ----------------------------------------------------
        # VALIDATE USD
        # ----------------------------------------------------

        if usd <= 0:

            print(
                "Navasan USD invalid."
                " Using old value."
            )

            usd = old_usd

        # ----------------------------------------------------
        # VALIDATE GOLD
        # ----------------------------------------------------

        if gold <= 0:

            print(
                "Navasan GOLD invalid."
                " Using old value."
            )

            gold = old_gold

        # ----------------------------------------------------
        # VALIDATE BTC
        # ----------------------------------------------------

        if btc <= 0:

            print(
                "Navasan BTC unavailable."
                " CoinGecko will be used."
            )

            btc = old_btc

        # ----------------------------------------------------
        # GOLD PERCENT
        # ----------------------------------------------------

        if gold > 0:

            gold_percent = calculate_percent(
                gold,
                gold_change
            )

        else:

            gold_percent = 0

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        print("")
        print(
            "NAVASAN FINAL VALUES"
        )

        print(
            "USD :",
            usd
        )

        print(
            "GOLD:",
            gold
        )

        print(
            "BTC :",
            btc
        )

        print(
            "GOLD %:",
            gold_percent
        )

        return {

            "usd": usd,

            "usd_change": usd_change,

            "usd_date": usd_date,

            "gold": {

                "price": gold,

                "change": gold_change,

                "change_percent":
                    gold_percent,

                "date": gold_date

            },

            "btc": btc,

            "btc_change": btc_change,

            "btc_date": btc_date,

            "success": True

        }

    except Exception as e:

        print("")
        print(
            "=" * 60
        )

        print(
            "NAVASAN MARKET ERROR"
        )

        print(
            "=" * 60
        )

        print(
            repr(e)
        )

        print(
            "=" * 60
        )

        return {

            "usd": old_usd,

            "usd_change": 0,

            "usd_date": "",

            "gold": {

                "price": old_gold,

                "change": 0,

                "change_percent": 0,

                "date": ""

            },

            "btc": old_btc,

            "btc_change": 0,

            "btc_date": "",

            "success": False

        }


# ============================================================
# BRS BACKUP
# USD + GOLD ONLY
# ============================================================

def get_brs_backup():

    old = load_old()

    old_usd = safe_int(
        old
        .get("iran", {})
        .get("usd", 0)
    )

    old_gold = safe_int(
        old
        .get("iran", {})
        .get("gold18", 0)
    )

    # --------------------------------------------------------
    # اگر BRS KEY نداریم
    # --------------------------------------------------------

    if not BRS_API_KEY:

        print(
            "BRS backup disabled."
        )

        return {

            "usd": old_usd,

            "gold": old_gold,

            "success": False

        }

    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"BRS backup attempt "
                f"{attempt}/{MAX_RETRIES}"
            )

            response = requests.get(

                BRS_URL,

                params={
                    "key":
                        BRS_API_KEY
                },

                headers=HEADERS,

                timeout=(
                    10,
                    25
                )
            )

            print(
                "BRS STATUS:",
                response.status_code
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(
                data,
                dict
            ):

                raise Exception(
                    "BRS response is invalid"
                )

            # ------------------------------------------------
            # GET LISTS
            # ------------------------------------------------

            currency = data.get(
                "currency",
                []
            )

            gold_list = data.get(
                "gold",
                []
            )

            # ------------------------------------------------
            # Nested data support
            # ------------------------------------------------

            if (
                not isinstance(
                    currency,
                    list
                )
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

            # ------------------------------------------------
            # USD
            # ------------------------------------------------

            usd_item = find_symbol(

                currency,

                [
                    "USD",
                    "USD_TMN",
                    "USD_IRR"
                ]

            )

            # ------------------------------------------------
            # GOLD
            # ------------------------------------------------

            gold_item = find_symbol(

                gold_list,

                [
                    "IR_GOLD_18K",
                    "GOLD_18K",
                    "GOLD18",
                    "18K"
                ]

            )

            usd = 0
            gold = 0

            # ------------------------------------------------
            # USD PRICE
            # ------------------------------------------------

            if usd_item:

                usd = safe_int(
                    usd_item.get(
                        "price"
                    ),
                    0
                )

            # ------------------------------------------------
            # GOLD PRICE
            # ------------------------------------------------

            if gold_item:

                gold = safe_int(
                    gold_item.get(
                        "price"
                    ),
                    0
                )

            # ------------------------------------------------
            # RESULT
            # ------------------------------------------------

            if usd <= 0:

                usd = old_usd

            if gold <= 0:

                gold = old_gold

            print("")
            print(
                "BRS BACKUP VALUES"
            )

            print(
                "USD :",
                usd
            )

            print(
                "GOLD:",
                gold
            )

            return {

                "usd": usd,

                "gold": gold,

                "success": True

            }

        except Exception as e:

            print(
                "BRS BACKUP ERROR:",
                repr(e)
            )

            if attempt < MAX_RETRIES:

                time.sleep(
                    RETRY_DELAY
                )

    # --------------------------------------------------------
    # BRS FAILED
    # --------------------------------------------------------

    print(
        "BRS backup unavailable."
    )

    return {

        "usd": old_usd,

        "gold": old_gold,

        "success": False

    }


# ============================================================
# COINGECKO BTC BACKUP
# ============================================================

def get_coingecko_btc():

    old = load_old()

    old_btc = safe_int(
        old
        .get("crypto", {})
        .get("btc", 0)
    )

    print("")
    print(
        "Connecting to CoinGecko..."
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"CoinGecko attempt "
                f"{attempt}/{MAX_RETRIES}"
            )

            response = requests.get(

                BTC_URL,

                headers=HEADERS,

                timeout=(
                    10,
                    20
                )

            )

            print(
                "COINGECKO STATUS:",
                response.status_code
            )

            if response.status_code == 429:

                print(
                    "CoinGecko rate limited."
                )

                break

            response.raise_for_status()

            data = response.json()

            btc = safe_int(

                data
                .get("bitcoin", {})
                .get("usd"),

                0

            )

            if btc > 0:

                print(
                    "CoinGecko BTC:",
                    btc
                )

                return btc

        except Exception as e:

            print(
                "COINGECKO ERROR:",
                repr(e)
            )

        if attempt < MAX_RETRIES:

            time.sleep(
                RETRY_DELAY
            )

    print(
        "CoinGecko unavailable."
        " Using previous BTC."
    )

    return old_btc


# ============================================================
# CHANGE
# ============================================================

def calc_change(
    new,
    old
):

    if old is None:
        return 0

    try:

        return (
            new - old
        )

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
        print(
            "Connecting to GitHub..."
        )

        old_file = requests.get(

            url,

            headers=headers,

            timeout=(
                10,
                20
            )

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

                sha = (
                    old_file
                    .json()
                    .get("sha")
                )

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
                    content.encode(
                        "utf-8"
                    )
                ).decode(
                    "utf-8"
                )

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

            timeout=(
                10,
                20
            )

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
print(
    "=" * 60
)

print(
    "MARKET UPDATE STARTED"
)

print(
    "=" * 60
)


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
# NAVASAN PRIMARY
# ============================================================

navasan = get_navasan_market()


# ============================================================
# INITIAL VALUES FROM NAVASAN
# ============================================================

usd = navasan["usd"]

gold = navasan["gold"]

btc = navasan["btc"]


usd_source = (
    "Navasan"
    if navasan["success"]
    else "Previous data"
)

gold_source = (
    "Navasan"
    if navasan["success"]
    else "Previous data"
)

btc_source = (
    "Navasan"
    if navasan["success"]
    else "Previous data"
)


# ============================================================
# BRS FALLBACK
# ============================================================

# اگر Navasan دلار یا طلا را نداد،
# BRS فقط همان موارد را تأمین می‌کند.

if (
    usd <= 0
    or gold <= 0
):

    print("")
    print(
        "Navasan USD/GOLD incomplete."
    )

    print(
        "Trying BRS backup..."
    )

    brs = get_brs_backup()

    if usd <= 0 and brs["usd"] > 0:

        usd = brs["usd"]

        usd_source = "BRS Backup"

    if gold <= 0 and brs["gold"] > 0:

        gold = brs["gold"]

        gold_source = "BRS Backup"


# ============================================================
# BTC COINGECKO FALLBACK
# ============================================================

if btc <= 0:

    print("")
    print(
        "Navasan BTC unavailable."
    )

    print(
        "Trying CoinGecko backup..."
    )

    btc = get_coingecko_btc()

    btc_source = (
        "CoinGecko Backup"
    )


# ============================================================
# ABSOLUTE SAFETY
# ============================================================

if usd <= 0:

    usd = safe_int(
        old_iran.get(
            "usd"
        ),
        0
    )

    usd_source = (
        "Previous data"
    )


if gold <= 0:

    gold = safe_int(
        old_iran.get(
            "gold18"
        ),
        0
    )

    gold_source = (
        "Previous data"
    )


if btc <= 0:

    btc = safe_int(
        old_crypto.get(
            "btc"
        ),
        0
    )

    btc_source = (
        "Previous data"
    )


# ============================================================
# CHANGES
# ============================================================

usd_change = calc_change(

    usd,

    old_iran.get(
        "usd"
    )

)


gold_change = calc_change(

    gold,

    old_iran.get(
        "gold18"
    )

)


btc_change = calc_change(

    btc,

    old_crypto.get(
        "btc"
    )

)


# ============================================================
# GOLD PERCENT
# ============================================================

if navasan["success"]:

    gold_percent = navasan[
        "gold"
    ].get(
        "change_percent",
        0
    )

else:

    old_gold_percent = (
        old_iran
        .get(
            "gold18_percent",
            0
        )
    )

    gold_percent = old_gold_percent


# ============================================================
# UPDATE DATE / TIME
# ============================================================

gold_date = (
    navasan["gold"]
    .get(
        "date",
        ""
    )
)

if not gold_date:

    gold_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# CREATE MARKET JSON
# ============================================================

market = {

    "iran": {

        "usd": usd,

        "usd_change":
            usd_change,

        "gold18":
            gold,

        "gold18_change":
            gold_change,

        "gold18_percent":
            gold_percent

    },

    "crypto": {

        "btc":
            btc,

        "btc_change":
            btc_change

    },

    "gold_update": {

        "date":
            gold_date,

        "time":
            navasan["gold"]
            .get(
                "date",
                ""
            )

    },

    "updated":
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

    "sources": {

        "usd":
            usd_source,

        "gold18":
            gold_source,

        "btc":
            btc_source

    }

}


# ============================================================
# PRINT FINAL MARKET
# ============================================================

print("")
print(
    "=" * 60
)

print(
    "FINAL MARKET JSON"
)

print(
    "=" * 60
)

print(
    json.dumps(
        market,
        ensure_ascii=False,
        indent=4
    )
)

print(
    "=" * 60
)


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
print(
    "=" * 60
)

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

print(
    "=" * 60
)



