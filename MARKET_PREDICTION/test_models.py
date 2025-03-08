import requests
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
import numpy as np

items = pd.read_csv("items.csv")["IDs"].values
np.random.shuffle(items)

BASE_URL = "https://esi.evetech.net/latest"
MARKET_REGION_ID = 10000002
JITA_STATION_ID = 60003760

def fetch_market_orders(region_id, item_id):
    url = f"{BASE_URL}/markets/{region_id}/orders/"
    params = {"type_id": item_id}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return [o for o in response.json() if o['location_id'] == JITA_STATION_ID]

def fetch_historical_prices(region_id, item_id):
    url = f"{BASE_URL}/markets/{region_id}/history/?datasource=tranquility&type_id={item_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def parse_market_orders(orders):
    buy_orders = [o for o in orders if o['is_buy_order']]
    sell_orders = [o for o in orders if not o['is_buy_order']]

    total_supply = sum(o['volume_remain'] for o in sell_orders)
    lowest_sell_price = min(o['price'] for o in sell_orders) if sell_orders else None

    total_demand = sum(o['volume_remain'] for o in buy_orders)
    highest_buy_price = max(o['price'] for o in buy_orders) if buy_orders else None

    return {
        "total_supply": total_supply,
        "lowest_sell_price": lowest_sell_price,
        "total_demand": total_demand,
        "highest_buy_price": highest_buy_price,
    }

calc_items = []
growths = []
prices = []
buy_prices = []

count = 0

for item in items:
    try:
        orders = fetch_market_orders(MARKET_REGION_ID, item)
        metrics = parse_market_orders(orders)

        historical_data = fetch_historical_prices(MARKET_REGION_ID, item)
        historical_df = pd.DataFrame(historical_data)

        historical_df['date'] = pd.to_datetime(historical_df['date'])
        historical_df['supply_demand_ratio'] = metrics['total_demand'] / metrics['total_supply']

        for lag in [1, 2, 3, 7]:
            historical_df[f'price_lag_{lag}'] = historical_df['average'].shift(lag)

        historical_df = historical_df.dropna()

        X = historical_df[[
            'supply_demand_ratio',
            'price_lag_1',
            'price_lag_2',
            'price_lag_3',
            'price_lag_7',
        ]]
        y = historical_df['average']

        model = RandomForestRegressor(random_state=42)
        model.fit(X, y)

        future_metrics = parse_market_orders(fetch_market_orders(MARKET_REGION_ID, item))
        future_features = pd.DataFrame({
            "supply_demand_ratio": [future_metrics['total_demand'] / future_metrics['total_supply']],
            "price_lag_1": [historical_df['average'].iloc[-1]],
            "price_lag_2": [historical_df['average'].iloc[-2]],
            "price_lag_3": [historical_df['average'].iloc[-3]],
            "price_lag_7": [historical_df['average'].iloc[-7]],
        })

        predicted_price = model.predict(future_features)[0]
        buy_price = metrics["lowest_sell_price"]
        calc_items.append(requests.get(f"{BASE_URL}/universe/types/{item}").json().get("name"))
        growths.append((predicted_price - buy_price) / buy_price)
        prices.append(predicted_price)
        buy_prices.append(buy_price)

        count += 1
        if count % 10 == 0:
            df = pd.DataFrame({"item": calc_items, "growth": growths, "price": prices, "buy_price": buy_prices})
            df = df.sort_values("growth", ascending=False)
            df.to_csv(r"MARKET_PREDICTION/investment_rankings.csv", index=False)
            print("Saved, batch", count / 10)

    except:
        pass