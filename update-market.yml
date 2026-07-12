      - name: Update Market
        run: |
          python << EOF
          import json
          import requests
          from datetime import datetime

          headers = {
              "User-Agent": "Mozilla/5.0"
          }

          # ==========================
          # ایران (دلار و طلا)
          # ==========================

          market_url = "https://brsapi.ir/Api/Market/Gold_Currency.php"

          r = requests.get(
              market_url,
              headers=headers,
              timeout=20
          )

          data = r.json()

          usd_iran = 0
          gold18 = 0

          for item in data:
              name = str(item.get("name", ""))

              if "دلار" in name and usd_iran == 0:
                  usd_iran = item["price"]

              if "طلای 18" in name or "طلای ۱۸" in name:
                  gold18 = item["price"]


          # ==========================
          # Exchange Rate API
          # ==========================

          api_key = "70907a9ff24bb63da4640a3a"

          fx_url = (
              f"https://v6.exchangerate-api.com/v6/"
              f"{api_key}/latest/USD"
          )

          fx = requests.get(
              fx_url,
              timeout=20
          ).json()


          rates = fx.get(
              "conversion_rates",
              {}
          )


          out = {

              "iran": {
                  "usd": usd_iran,
                  "gold18": gold18
              },

              "global": {
                  "USD": 1,
                  "EUR": rates.get("EUR"),
                  "GBP": rates.get("GBP"),
                  "TRY": rates.get("TRY"),
                  "AED": rates.get("AED"),
                  "RUB": rates.get("RUB")
              },

              "updated": datetime.now().strftime(
                  "%Y-%m-%d %H:%M:%S"
              )
          }


          with open(
              "market.json",
              "w",
              encoding="utf8"
          ) as f:

              json.dump(
                  out,
                  f,
                  ensure_ascii=False,
                  indent=2
              )

          EOF
