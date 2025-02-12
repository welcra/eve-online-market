import requests
import pandas as pd

regions_url = "https://esi.evetech.net/latest/universe/regions"

response = requests.get(regions_url)

regions = response.json()

opps = []

for region in [regions[1]]:
    region_info_url = "https://esi.evetech.net/latest/universe/regions/{}".format(region)

    response = requests.get(region_info_url)

    region_info = response.json()

    name = region_info.get("name")

    df = pd.read_csv(r"C:\Users\arnav\OneDrive\Documents\EVE_QUANT\EVE_ARBITRAGE\orders\{}_{}_orders.csv".format(name, region))

    buys = df[df["orderType"] == True]

    sells = df[df["orderType"] == False]

    items = buys["item"].unique()

    for i in items:
        item_buys = buys[buys["item"] == i]
        if item_buys.empty:
            continue
        buy = item_buys.loc[item_buys["price"].idxmax()]
        item_sells = sells[sells["item"] == i]
        if item_sells.empty:
            continue
        sell = item_sells.loc[item_sells["price"].idxmin()]
        if buy.get("price")>sell.get("price"):
            opps.append([buy, sell]) #CHANGE TO GREATEST PROFIT NOT CHANGE IN PRICE


sorted_opps = []

for buy, sell in opps:
    buy_price = buy.get("price")
    sell_price = sell.get("price")

    if buy_price and sell_price:
        percent_change = ((buy_price - sell_price) / sell_price) * 100

        sorted_opps.append({
            "buy_order": buy.to_dict(),
            "sell_order": sell.to_dict(),
            "percent_change": percent_change
        })

sorted_opps = sorted(sorted_opps, key=lambda x: abs(x["percent_change"]), reverse=True)

opps_df = pd.DataFrame(sorted_opps)

opps_df.to_csv(r"C:\Users\arnav\OneDrive\Documents\EVE_QUANT\EVE_ARBITRAGE\opportunities.csv", index=False)