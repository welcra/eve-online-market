import pandas as pd
import requests
import json

import esi
import arbitrage_opps

opps = pd.read_csv(r"C:\Users\arnav\OneDrive\Documents\EVE_QUANT\EVE_ARBITRAGE\opportunities.csv")

data = {}

for i in range(len(opps)):
    buy_order_str = str(opps.iloc[i]["buy_order"]).strip().replace("'", '"').replace("True", "true")
    buy = json.loads(buy_order_str)
    sell_order_str = str(opps.iloc[i]["sell_order"]).strip().replace("'", '"').replace("False", "false")
    sell = json.loads(sell_order_str)
    vbought = 0

    if buy["volume"] > sell["volume"]:
        vbought = sell["volume"]
    else:
        vbought = buy["volume"]

    max_profit = buy["price"]*vbought - sell["price"]*vbought

    data[str(i)] = (max_profit, sell["price"]*vbought, buy["location"], buy["price"], buy["system"], buy["item"], buy["volume"], sell["location"], sell["price"], sell["system"], sell["item"], sell["volume"], vbought, opps.iloc[i]["percent_change"])


max_profit = max(item[0] for item in data.values())
min_profit = min(item[0] for item in data.values())
max_capital = max(item[1] for item in data.values())
min_capital = min(item[1] for item in data.values())

def balance_key(item):
    profit, capital, a, b, c, d, e, f, g, h, i, j, k, l = item[1]
    
    norm_profit = (profit - min_profit) / (max_profit - min_profit)
    norm_capital = (capital - min_capital) / (max_capital - min_capital)
    combined_score = norm_profit - norm_capital
    
    return combined_score

data = sorted(data.items(), key=balance_key, reverse=True)

for i in data:
    info = i[1]

    sloc = requests.get("https://esi.evetech.net/latest/universe/stations/{}".format(info[2])).json().get("name")
    bloc = requests.get("https://esi.evetech.net/latest/universe/stations/{}".format(info[7])).json().get("name")

    if sloc and bloc:

        if "jita" in sloc.lower() or "jita" in bloc.lower():
            print("Profit:", f"{info[0]:,}")
            print("Capital Needed:", f"{info[1]:,}")
            print("Percent Change:", str(info[-1])+"%")
            print("Volume:", f"{info[-2]:,}")
            print("Item:", requests.get("https://esi.evetech.net/latest/universe/types/{}".format(info[5])).json().get("name"))
            print("Buy at:", bloc)
            print("Sell at:", sloc)
            print("--------------------------------------------------------------------")