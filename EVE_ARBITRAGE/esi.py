import requests
import pandas as pd

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

regions_url = "https://esi.evetech.net/latest/universe/regions"

response = requests.get(regions_url)

regions = response.json()

for region in [regions[1]]:

    region_info_url = "https://esi.evetech.net/latest/universe/regions/{}".format(region)

    response = requests.get(region_info_url)

    region_info = response.json()

    name = region_info.get("name")

    orders_url = "https://esi.evetech.net/latest/markets/{}/orders/".format(region)

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
    locations = []
    prices = []
    systems = []
    types = []
    volumes = []

    for i in orders:
        ordertypes.append(i.get("is_buy_order"))
        locations.append(i.get("location_id"))
        prices.append(i.get("price"))
        systems.append(i.get("system_id"))
        types.append(i.get("type_id"))
        volumes.append(i.get("volume_remain"))

    df = pd.DataFrame({"orderType":ordertypes, "location":locations, "price":prices, "system":systems, "item":types, "volume":volumes})

    df.to_csv(r"C:\Users\arnav\OneDrive\Documents\EVE_QUANT\EVE_ARBITRAGE\orders\{}_{}_orders.csv".format(name, region), index=False)