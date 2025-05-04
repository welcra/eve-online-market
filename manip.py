import requests
import pandas as pd
import time

ISK_BUDGET = 130_000_000
BROKER_FEE = 0.03
TAX_RATE = 0.015

JITA_REGION_ID = 10000002
JITA_STATION_ID = 60003760
JITA_SYSTEM_ID = 30000142

def get_item_names():
    url = "https://www.fuzzwork.co.uk/dump/latest/invTypes.csv"
    df = pd.read_csv(url)
    return df[['typeID', 'typeName']]

def get_market_orders(type_id):
    url = f"https://esi.evetech.net/latest/markets/{JITA_REGION_ID}/orders/?type_id={type_id}"
    try:
        response = requests.get(url).json()
        return [o for o in response if o['location_id'] == JITA_STATION_ID]
    except:
        return []

def estimate_real_relist_price(sell_orders, min_count=3):
    sorted_orders = sorted([o['price'] for o in sell_orders if o['is_buy_order'] is False])
    return sorted_orders[min_count] if len(sorted_orders) > min_count else None

def estimate_profit(buy_price, relist_price, volume):
    total_cost = buy_price * volume * (1 + BROKER_FEE)
    total_sale = relist_price * volume * (1 - TAX_RATE)
    return total_sale - total_cost, (total_sale - total_cost) / total_cost

def find_opportunities():
    items = get_item_names().sample(frac=1)
    results = []

    for _, row in items.iterrows():
        type_id, name = row['typeID'], row['typeName']
        orders = get_market_orders(type_id)
        if not orders:
            continue

        buy_orders = [o for o in orders if o['is_buy_order']]
        sell_orders = [o for o in orders if not o['is_buy_order']]

        if not buy_orders or not sell_orders:
            continue

        highest_buy = max([o['price'] for o in buy_orders])
        lowest_sell = min([o['price'] for o in sell_orders])
        relist_price = estimate_real_relist_price(sell_orders)

        if not relist_price or relist_price <= highest_buy:
            continue

        volume = sum([o['volume_remain'] for o in sell_orders if o['price'] <= relist_price])
        total_cost = lowest_sell * volume

        if volume == 0 or total_cost > ISK_BUDGET or volume > 10:
            continue

        profit, roi = estimate_profit(lowest_sell, relist_price, volume)

        if profit > 10_000_000 and roi > 0.2:
            results.append({
                "Item": name,
                "Buy Price": lowest_sell,
                "Relist Price": relist_price,
                "Volume": volume,
                "Total Cost": int(total_cost),
                "Estimated Profit": int(profit),
                "ROI": f"{roi:.2%}"
            })
            print(f"Item: {name}, Buy Price: {lowest_sell}, Relist Price: {relist_price}, Volume: {volume}, Total Cost: {int(total_cost)}, Estimated Profit: {int(profit)}, ROI: {roi:.2%}")

    return pd.DataFrame(results).sort_values(by="ROI", ascending=False)

if __name__ == "__main__":
    df = find_opportunities()
    print(df.to_string(index=False))
