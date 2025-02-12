import requests
import pandas as pd

orders_url = "https://esi.evetech.net/latest/markets/10000002/orders/"

orders = []
page = 1
while True:
    response = requests.get(f"{orders_url}?page={page}")
    if response.status_code != 200:
        print(f"Failed to fetch orders for page {page}: {response.status_code}")
        break
    
    orders.extend(response.json())

    print(page/int(response.headers.get("X-Pages", 1)))
    
    if page >= int(response.headers.get("X-Pages", 1)):
        break
    
    page += 1


ordertypes = []
prices = []
types = []
volumes = []

for i in orders:
    if i.get("location_id") == 60003760:
        ordertypes.append(i.get("is_buy_order"))
        prices.append(i.get("price"))
        types.append(i.get("type_id"))
        volumes.append(i.get("volume_remain"))

df = pd.DataFrame({"orderType":ordertypes, "price":prices, "item":types, "volume":volumes})

df.to_csv(r"C:\Users\arnav\OneDrive\Documents\EVE_QUANT\MARKET_PREDICTION\JITA_orders.csv", index=False)