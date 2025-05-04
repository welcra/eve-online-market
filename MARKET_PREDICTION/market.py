import pandas as pd
import requests

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