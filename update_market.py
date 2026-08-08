import requests
import json
import os
import base64
import time
from datetime import datetime


# ============================================================
# MARKET UPDATE
# Navasan     -> USD + Gold 18K
# BRS         -> USD + Gold backup
# CoinGecko   -> BTC + BTC backup
# GitHub      -> market.json
#
# USDT / ETH / DOGE / سایر ارزها عمداً استفاده نمی‌شوند.
# ============================================================


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


# ============================================================
# SETTINGS
# ============================================================

DATA_FILE = "market.json"

GITHUB_REPO = "DiamondXGEM/market-data"
GITHUB_FILE = "market.json"


# ============================================================
# API URLS
# ============================================================

NAVASAN_URL = (
    "http://api.navasan.tech/latest/"
)

BRS_URL = (
    "https://api.brsapi.ir/"
    "Market/Gold_Currency.php"
)

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/"
    "simple/price"
)


# ============================================================
# NETWORK SETTINGS
# ============================================================

MAX_RETRIES = 2
RETRY_DELAY = 2


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
# LOGGING
# فقط لاگ‌های ضروری
# ============================================================

def log(
    message
):

    print(
        f"[MARKET] {message}"
    )


# ============================================================
# LOAD OLD DATA
# ============================================================

def load_old():

    if not os.path.exists(
        DATA_FILE
    ):

        return {}

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(
                f
            )

        if isinstance(
            data,
            dict
        ):

            return data

    except Exception as e:

        log(
            f"Old JSON read failed: {repr(e)}"
        )

    return {}


# ============================================================
# SAFE INTEGER
# ============================================================

def safe_int(
    value,
    default=0
):

    if value is None:
        return default

    if isinstance(
        value,
        bool
    ):

        return default

    try:

        text = str(
            value
        ).strip()

        if not text:

            return default

        text = (
            text
            .replace(",", "")
            .replace("٬", "")
            .replace(" ", "")
        )

        return int(
            float(text)
        )

    except Exception:

        return default


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(
    value,
    default=0
):

    if value is None:
        return default

    try:

        text = str(
            value
        ).strip()

        if not text:

            return default

        text = (
            text
            .replace(",", "")
            .replace("٬", "")
            .replace(" ", "")
        )

        return float(
            text
        )

    except Exception:

        return default


# ============================================================
# HTTP JSON REQUEST
# محدود و بدون Flood کردن Railway Logs
# ============================================================

def get_json(
    url,
    params=None,
    timeout=(8, 20)
):

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=timeout
            )

            response.raise_for_status()

            return response.json()

        except Exception as e:

            last_error = e

            if attempt < MAX_RETRIES:

                time.sleep(
                    RETRY_DELAY
                )

    raise last_error


# ============================================================
# GENERIC VALUE EXTRACTOR
#
# فقط کلیدهایی که خودمان مشخص می‌کنیم بررسی می‌شوند.
# داده‌های دیگر Navasan کاملاً Ignore می‌شوند.
# ============================================================

def find_value(
    data,
    allowed_keys
):

    if not isinstance(
        data,
        dict
    ):

        return 0

    allowed = {
        str(key).lower()
        for key in allowed_keys
    }


    # --------------------------------------------------------
    # Direct keys
    # --------------------------------------------------------

    for key in allowed_keys:

        if key not in data:

            continue

        item = data.get(
            key
        )


        # مقدار مستقیم
        if not isinstance(
            item,
            dict
        ):

            value = safe_int(
                item
            )

            if value > 0:

                return value


        # مقدار داخل object
        if isinstance(
            item,
            dict
        ):

            for value_key in (
                "value",
                "price",
                "sell",
                "close"
            ):

                value = safe_int(
                    item.get(
                        value_key
                    )
                )

                if value > 0:

                    return value


    # --------------------------------------------------------
    # Recursive search
    #
    # فقط allowed_keys بررسی می‌شوند.
    # --------------------------------------------------------

    def recursive(
        obj
    ):

        if isinstance(
            obj,
            dict
        ):

            for key, value in obj.items():

                key_lower = str(
                    key
                ).lower()


                if key_lower in allowed:

                    if isinstance(
                        value,
                        dict
                    ):

                        for value_key in (
                            "value",
                            "price",
                            "sell",
                            "close"
                        ):

                            number = safe_int(
                                value.get(
                                    value_key
                                )
                            )

                            if number > 0:

                                return number

                    else:

                        number = safe_int(
                            value
                        )

                        if number > 0:

                            return number


                # فقط برای پیدا کردن کلیدهای مجاز
                # داخل ساختارهای تو در تو ادامه می‌دهیم.

                result = recursive(
                    value
                )

                if result > 0:

                    return result


        elif isinstance(
            obj,
            list
        ):

            for item in obj:

                result = recursive(
                    item
                )

                if result > 0:

                    return result


        return 0


    return recursive(
        data
    )


# ============================================================
# NAVASAN
#
# فقط:
# USD
# GOLD 18K
#
# BTC / USDT / ETH / DOGE و غیره بررسی نمی‌شوند.
# ============================================================

def get_navasan():

    try:

        data = get_json(
            NAVASAN_URL,
            params={
                "api_key":
                    NAVASAN_API_KEY
            },
            timeout=(
                8,
                20
            )
        )


        if not isinstance(
            data,
            dict
        ):

            raise Exception(
                "Navasan returned invalid JSON"
            )


        # ----------------------------------------------------
        # USD
        # ----------------------------------------------------

        usd = find_value(
            data,
            [
                "usd_sell",
                "usd",
                "usd_sell_price",
                "dollar",
                "dollar_sell"
            ]
        )


        # ----------------------------------------------------
        # GOLD 18K
        # ----------------------------------------------------

        gold = find_value(
            data,
            [
                "18ayar",
                "gold18",
                "gold_18k",
                "gold18k",
                "18k"
            ]
        )


        # ----------------------------------------------------
        # فقط دو مقدار بالا استفاده می‌شوند.
        # ----------------------------------------------------

        return {
            "usd": usd,
            "gold": gold
        }


    except Exception as e:

        log(
            f"Navasan failed: {repr(e)}"
        )

        return {
            "usd": 0,
            "gold": 0
        }


# ============================================================
# BRS BACKUP
#
# فقط USD + GOLD
# ============================================================

def get_brs():

    if not BRS_API_KEY:

        return {
            "usd": 0,
            "gold": 0
        }


    try:

        data = get_json(
            BRS_URL,
            params={
                "key":
                    BRS_API_KEY
            },
            timeout=(
                8,
                20
            )
        )


        if not isinstance(
            data,
            dict
        ):

            raise Exception(
                "Invalid BRS response"
            )


        currency = data.get(
            "currency",
            []
        )

        gold_list = data.get(
            "gold",
            []
        )


        # ----------------------------------------------------
        # Nested data support
        # ----------------------------------------------------

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

            nested = data[
                "data"
            ]

            currency = nested.get(
                "currency",
                []
            )

            gold_list = nested.get(
                "gold",
                []
            )


        # ----------------------------------------------------
        # USD ONLY
        # ----------------------------------------------------

        usd = 0


        if isinstance(
            currency,
            list
        ):

            for item in currency:

                if not isinstance(
                    item,
                    dict
                ):

                    continue


                symbol = str(
                    item.get(
                        "symbol",
                        ""
                    )
                ).upper()


                if symbol in (
                    "USD",
                    "USD_TMN",
                    "USD_IRR"
                ):

                    usd = safe_int(
                        item.get(
                            "price"
                        )
                    )

                    if usd > 0:

                        break


        # ----------------------------------------------------
        # GOLD 18K ONLY
        # ----------------------------------------------------

        gold = 0


        if isinstance(
            gold_list,
            list
        ):

            for item in gold_list:

                if not isinstance(
                    item,
                    dict
                ):

                    continue


                symbol = str(
                    item.get(
                        "symbol",
                        ""
                    )
                ).upper()


                if symbol in (
                    "IR_GOLD_18K",
                    "GOLD_18K",
                    "GOLD18",
                    "18K"
                ):

                    gold = safe_int(
                        item.get(
                            "price"
                        )
                    )

                    if gold > 0:

                        break


        return {
            "usd": usd,
            "gold": gold
        }


    except Exception as e:

        log(
            f"BRS backup failed: {repr(e)}"
        )

        return {
            "usd": 0,
            "gold": 0
        }


# ============================================================
# COINGECKO
#
# فقط Bitcoin/USD
# ============================================================

def get_btc():

    try:

        data = get_json(
            COINGECKO_URL,
            params={
                "ids":
                    "bitcoin",
                "vs_currencies":
                    "usd"
            },
            timeout=(
                8,
                15
            )
        )


        btc = safe_int(
            data
            .get(
                "bitcoin",
                {}
            )
            .get(
                "usd"
            )
        )


        if btc <= 0:

            raise Exception(
                "Invalid BTC value"
            )


        return btc


    except Exception as e:

        log(
            f"CoinGecko failed: {repr(e)}"
        )

        return 0


# ============================================================
# CHANGE
# ============================================================

def calc_change(
    new,
    old
):

    new = safe_int(
        new
    )

    old = safe_int(
        old
    )


    if old <= 0:

        return 0


    return new - old


# ============================================================
# GOLD PERCENT
# ============================================================

def calc_percent(
    current,
    change
):

    current = safe_float(
        current
    )

    change = safe_float(
        change
    )


    if current <= 0:

        return 0


    previous = (
        current - change
    )


    if previous <= 0:

        return 0


    return round(
        (
            change
            / previous
        ) * 100,
        2
    )


# ============================================================
# BUILD MARKET
# ============================================================

def build_market():

    old = load_old()


    old_iran = old.get(
        "iran",
        {}
    )


    old_crypto = old.get(
        "crypto",
        {}
    )


    old_usd = safe_int(
        old_iran.get(
            "usd"
        )
    )


    old_gold = safe_int(
        old_iran.get(
            "gold18"
        )
    )


    old_btc = safe_int(
        old_crypto.get(
            "btc"
        )
    )


    # ========================================================
    # 1. NAVASAN
    # ========================================================

    navasan = get_navasan()


    usd = navasan[
        "usd"
    ]


    gold = navasan[
        "gold"
    ]


    usd_source = (
        "Navasan"
        if usd > 0
        else ""
    )


    gold_source = (
        "Navasan"
        if gold > 0
        else ""
    )


    # ========================================================
    # 2. BRS BACKUP
    # ========================================================

    if (
        usd <= 0
        or gold <= 0
    ):

        brs = get_brs()


        if (
            usd <= 0
            and brs["usd"] > 0
        ):

            usd = brs[
                "usd"
            ]

            usd_source = (
                "BRS Backup"
            )


        if (
            gold <= 0
            and brs["gold"] > 0
        ):

            gold = brs[
                "gold"
            ]

            gold_source = (
                "BRS Backup"
            )


    # ========================================================
    # 3. BTC FROM COINGECKO
    # ========================================================

    btc = get_btc()


    if btc > 0:

        btc_source = (
            "CoinGecko"
        )

    else:

        btc = old_btc

        btc_source = (
            "Previous data"
        )


    # ========================================================
    # 4. LAST RESORT FOR USD
    # ========================================================

    if usd <= 0:

        usd = old_usd

        usd_source = (
            "Previous data"
        )


    # ========================================================
    # 5. LAST RESORT FOR GOLD
    # ========================================================

    if gold <= 0:

        gold = old_gold

        gold_source = (
            "Previous data"
        )


    # ========================================================
    # CHANGES
    # ========================================================

    usd_change = calc_change(
        usd,
        old_usd
    )


    gold_change = calc_change(
        gold,
        old_gold
    )


    btc_change = calc_change(
        btc,
        old_btc
    )


    # ========================================================
    # GOLD PERCENT
    # ========================================================

    # چون API نوسان ممکن است change را در ساختار متفاوتی
    # برگرداند، در صورت نبودن مقدار معتبر، مقدار قبلی حفظ می‌شود.

    old_gold_percent = safe_float(
        old_iran.get(
            "gold18_percent",
            0
        )
    )


    gold_percent = old_gold_percent


    # اگر مقدار جدید طلا از Navasan آمده،
    # فعلاً درصد را بر اساس تغییر نسبت به market.json
    # محاسبه می‌کنیم.

    if (
        gold > 0
        and old_gold > 0
    ):

        gold_percent = round(
            (
                (
                    gold
                    - old_gold
                )
                / old_gold
            ) * 100,
            2
        )


    # ========================================================
    # GOLD UPDATE
    # ========================================================

    old_gold_update = old.get(
        "gold_update",
        {}
    )


    gold_date = old_gold_update.get(
        "date",
        ""
    )


    gold_time = old_gold_update.get(
        "time",
        ""
    )


    # ========================================================
    # FINAL MARKET JSON
    #
    # فقط فیلدهایی که Yalda.py نیاز دارد.
    # ========================================================

    market = {

        "iran": {

            "usd":
                usd,

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
                gold_time

        },

        "updated":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    }


    # ========================================================
    # SOURCE LOG ONLY
    # داخل JSON ذخیره نمی‌شود.
    # ========================================================

    log(
        "Sources: "
        f"USD={usd_source} | "
        f"GOLD={gold_source} | "
        f"BTC={btc_source}"
    )


    return market


# ============================================================
# SAVE JSON
# ============================================================

def save_market(
    market
):

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


        return True


    except Exception as e:

        log(
            f"JSON save failed: {repr(e)}"
        )

        return False


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

        # ----------------------------------------------------
        # Get current GitHub file
        # ----------------------------------------------------

        current = requests.get(
            url,
            headers=headers,
            timeout=15
        )


        if current.status_code not in (
            200,
            404
        ):

            log(
                "GitHub GET failed: "
                f"{current.status_code}"
            )

            return False


        sha = None


        if current.status_code == 200:

            sha = current.json().get(
                "sha"
            )


        # ----------------------------------------------------
        # Read local JSON
        # ----------------------------------------------------

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read()


        # ----------------------------------------------------
        # Payload
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

            payload[
                "sha"
            ] = sha


        # ----------------------------------------------------
        # PUT
        # ----------------------------------------------------

        response = requests.put(
            url,
            headers=headers,
            json=payload,
            timeout=15
        )


        if response.status_code in (
            200,
            201
        ):

            log(
                "GitHub updated successfully"
            )

            return True


        log(
            "GitHub update failed: "
            f"{response.status_code}"
        )

        return False


    except Exception as e:

        log(
            f"GitHub error: {repr(e)}"
        )

        return False


# ============================================================
# MAIN
# ============================================================

def main():

    log(
        "Update started"
    )


    market = build_market()


    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    if not save_market(
        market
    ):

        raise RuntimeError(
            "market.json save failed"
        )


    # --------------------------------------------------------
    # GitHub
    # --------------------------------------------------------

    github_ok = push_github()


    # --------------------------------------------------------
    # One compact summary
    # --------------------------------------------------------

    log(
        "USD="
        f"{market['iran']['usd']:,}"
        " | GOLD="
        f"{market['iran']['gold18']:,}"
        " | BTC="
        f"{market['crypto']['btc']:,}"
    )


    if github_ok:

        log(
            "Update completed successfully"
        )

    else:

        log(
            "JSON saved locally, "
            "but GitHub update failed"
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as e:

        log(
            f"FATAL ERROR: {repr(e)}"
        )

        raise



