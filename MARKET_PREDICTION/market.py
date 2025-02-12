import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import requests

orders = pd.read_csv(r"MARKET_PREDICTION\JITA_orders.csv")

for i in orders["item"].unique():

    tritaniums = orders[orders["item"] == i]
    tr_sells = tritaniums[tritaniums["orderType"] == False]
    tr_buys = tritaniums[tritaniums["orderType"] == True]

    if tr_sells.empty or tr_buys.empty:
        continue

    buys_X = tr_buys["volume"].values.reshape(-1, 1)
    buys_Y = tr_buys["price"].values

    sells_X = tr_sells["volume"].values.reshape(-1, 1)
    sells_Y = tr_sells["price"].values

    buy_model = LinearRegression()
    buy_model.fit(buys_X, buys_Y)

    sell_model = LinearRegression()
    sell_model.fit(sells_X, sells_Y)


    m_buy, b_buy = buy_model.coef_[0], buy_model.intercept_
    m_sell, b_sell = sell_model.coef_[0], sell_model.intercept_

    if m_buy != m_sell and m_buy < 0 and m_sell > 0:
        intersection_volume = (b_sell - b_buy) / (m_buy - m_sell)
        intersection_price = buy_model.predict([[intersection_volume]])[0]
        if intersection_volume > 0 and intersection_price > 0:
            print(f"Sell {requests.get("https://esi.evetech.net/latest/universe/types/{}".format(i)).json().get("name")} with volume: {intersection_volume}, price: {intersection_price}")