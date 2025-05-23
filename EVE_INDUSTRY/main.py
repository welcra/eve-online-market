import pandas as pd
import requests
import numpy as np
import talib
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Dropout
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import inspect

BASE_URL = "https://esi.evetech.net/latest" 
MARKET_REGION_ID = 10000002
JITA_STATION_ID = 60003760

scaler = StandardScaler() 

def fetch_historical_prices(region_id, item_id):
    url = f"{BASE_URL}/markets/{region_id}/history/?datasource=tranquility&type_id={item_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json() 

def create_lstm_dataset(data, window_size=30):
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i + window_size])
        y.append(data[i + window_size, 0])
    
    X = np.array(X)
    y = np.array(y) 
    
    return X, y

def fetch_market_orders(region_id, item_id):
    url = f"{BASE_URL}/markets/{region_id}/orders/"
    params = {"type_id": item_id}
    response = requests.get(url, params=params) 
    response.raise_for_status()
    return response.json()

items = pd.read_csv("items.csv")["IDs"].values
np.random.shuffle(items)

names = []
buy_prices = []
sell_prices = []
growths = []

for item in items:
    try:
        historical_data = fetch_historical_prices(MARKET_REGION_ID, item)
        historical_df = pd.DataFrame(historical_data)

        tadf = historical_df

        open_ = np.array(tadf["average"].values, dtype=np.float64)
        high = np.array(tadf["highest"].values, dtype=np.float64)
        low = np.array(tadf["lowest"].values, dtype=np.float64)
        close = np.array(tadf["average"].values, dtype=np.float64)

        candlestick_patterns = ["CDL2CROWS", "CDL3BLACKCROWS", "CDL3INSIDE", "CDL3LINESTRIKE", "CDL3OUTSIDE", 
                                "CDL3STARSINSOUTH", "CDL3WHITESOLDIERS", "CDLABANDONEDBABY", "CDLADVANCEBLOCK", 
                                "CDLBELTHOLD", "CDLBREAKAWAY", "CDLCLOSINGMARUBOZU", "CDLCONCEALBABYSWALL", "CDLCOUNTERATTACK", 
                                "CDLDARKCLOUDCOVER", "CDLDOJI", "CDLDOJISTAR", "CDLDRAGONFLYDOJI", "CDLENGULFING", 
                                "CDLEVENINGDOJISTAR", "CDLEVENINGSTAR", "CDLGAPSIDESIDEWHITE", "CDLGRAVESTONEDOJI", "CDLHAMMER", 
                                "CDLHANGINGMAN", "CDLHARAMI", "CDLHARAMICROSS", "CDLHIGHWAVE", "CDLHIKKAKE", "CDLHIKKAKEMOD", 
                                "CDLHOMINGPIGEON", "CDLIDENTICAL3CROWS", "CDLINNECK", "CDLINVERTEDHAMMER", "CDLKICKING", 
                                "CDLKICKINGBYLENGTH", "CDLLADDERBOTTOM", "CDLLONGLEGGEDDOJI", "CDLLONGLINE", "CDLMARUBOZU", 
                                "CDLMATCHINGLOW", "CDLMATHOLD", "CDLMORNINGDOJISTAR", "CDLMORNINGSTAR", "CDLONNECK", 
                                "CDLPIERCING", "CDLRICKSHAWMAN", "CDLRISEFALL3METHODS", "CDLSEPARATINGLINES", "CDLSHOOTINGSTAR", 
                                "CDLSHORTLINE", "CDLSPINNINGTOP", "CDLSTALLEDPATTERN", "CDLSTICKSANDWICH", "CDLTAKURI", 
                                "CDLTASUKIGAP", "CDLTHRUSTING", "CDLTRISTAR", "CDLUNIQUE3RIVER", "CDLUPSIDEGAP2CROWS", 
                                "CDLXSIDEGAP3METHODS"] 

        for pattern in candlestick_patterns:
            tadf[pattern] = getattr(talib, pattern)(open_, high, low, close) 

        indicators = talib.get_functions() 

        for indicator in indicators:
            if "CDL" in indicator: 
                continue

            try:
                func = getattr(talib, indicator)
                signature = inspect.signature(func)
                params = signature.parameters

                price_params = []
                other_params = {}

                for name, param in params.items():
                    if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                        if name in ["open", "high", "low", "close", "adjclose", "volume", "real"]:
                            price_params.append(name)
                        else:
                            if "timeperiod" in name:
                                other_params[name] = 14
                            elif "fastperiod" in name or "slowperiod" in name:
                                other_params[name] = 12 
                            elif "signalperiod" in name:
                                other_params[name] = 9
                            elif "matype" in name:
                                other_params[name] = 0
                            else:
                                other_params[name] = 5

                price_data = []
                for p in price_params:
                    if p == "close" or p == "average":
                        price_data.append(tadf["average"])
                    elif p == "adjclose" and "average" in tadf.columns:
                        price_data.append(tadf["average"])
                    elif p == "high" and "highest" in tadf.columns:
                        price_data.append(tadf["highest"])
                    elif p == "low" and "lowest" in tadf.columns:
                        price_data.append(tadf["lowest"])
                    elif p == "volume" and "volume" in tadf.columns:
                        price_data.append(tadf["volume"])
                    elif p == "real" and "average" in tadf.columns:
                        price_data.append(tadf["average"])

                if price_data:
                    result = func(*price_data, **other_params)

                    if isinstance(result, tuple):
                        for i, r in enumerate(result):
                            tadf[f"{indicator}_{i}"] = r
                    else:
                        tadf[indicator] = result

            except Exception as e:
                print(f"Error processing indicator {indicator}: {e}")
                continue

        if len(tadf) < 100:
            continue 

        feature_columns = ["average", "highest", "lowest"]
        for pattern in candlestick_patterns:
            feature_columns.append(pattern)

        data = tadf[feature_columns].values
        data = scaler.fit_transform(data) 

        X, y = create_lstm_dataset(data)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False) 

        model = Sequential()
        model.add(LSTM(units=150, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
        model.add(Dropout(0.2))
        model.add(LSTM(units=150))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))

        model.compile(optimizer=Adam(), loss="mean_squared_error")

        model.fit(X_train, y_train, epochs=50, batch_size=32) 

        predictions = model.predict(X_test)

        predictions_reshaped = np.reshape(predictions, (predictions.shape[0], 1))

        predictions_with_fake_features = np.repeat(predictions_reshaped, data.shape[1], axis=1) 

        predictions_inverse = scaler.inverse_transform(predictions_with_fake_features)

        predictions_final = predictions_inverse[:, 0]

        y_reshaped = np.reshape(y_test, (y_test.shape[0], 1))

        y_with_fake_features = np.repeat(y_reshaped, data.shape[1], axis=1)

        y_inverse = scaler.inverse_transform(y_with_fake_features) 

        y_final = y_inverse[:, 0]

        import math

        rmse = math.sqrt(mean_squared_error(predictions_final, y_final))
        mae = mean_absolute_error(y_test, y_final)

        print(f"RMSE: {rmse}")
        print(f"MAE: {mae}")

        plt.figure(figsize=(14, 7))
        plt.plot(y_final, label="Real Values", color="blue")
        plt.plot(predictions_final, label="Predictions", color="red")
        plt.title(f"Predicted vs Real Prices for Item {item}") 
        plt.xlabel("Time")
        plt.ylabel("Price")
        plt.legend()
        plt.show()
        latest_data = data[-30:]

        latest_data = np.reshape(latest_data, (1, latest_data.shape[0], latest_data.shape[1]))

        predicted_price = model.predict(latest_data)

        predicted_price_reshaped = np.reshape(predicted_price, (predicted_price.shape[0], 1))
        predicted_price_with_fake_features = np.repeat(predicted_price_reshaped, data.shape[1], axis=1) 
        predicted_price_final = scaler.inverse_transform(predicted_price_with_fake_features)

        tomorrows_price = predicted_price_final[0, 0]

        name = requests.get("https://esi.evetech.net/latest/universe/types/{}".format(item)).json().get("name") 

        orders = fetch_market_orders(MARKET_REGION_ID, item)

        buy_orders = [o for o in orders if o['is_buy_order']]
        sell_orders = [o for o in orders if not o['is_buy_order']]

        total_supply = sum(o['volume_remain'] for o in sell_orders)
        lowest_sell_price = min(o['price'] for o in sell_orders) if sell_orders else None 

        total_demand = sum(o['volume_remain'] for o in buy_orders)
        highest_buy_price = max(o['price'] for o in buy_orders) if buy_orders else None

        if total_demand > total_supply and tomorrows_price > lowest_sell_price: 
            names.append(name)
            buy_prices.append(lowest_sell_price) 
            sell_prices.append(tomorrows_price)
            growths.append((tomorrows_price-lowest_sell_price)/lowest_sell_price)

        if len(names) % 3 == 0 and len(names) != 0:
            investments = pd.DataFrame({"Item":names, "BuyFor":buy_prices, "SellFor":sell_prices, "Growth":growths})
            investments.to_csv("investments.csv", index=False) 


    except Exception as e:
        print(f"Error processing item {item}: {e}")
        continue