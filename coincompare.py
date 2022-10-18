from google.cloud import storage
from common import get_secret_data, get_crypto_bucket
import json
import requests
import time

CC_URL_STEM = 'https://min-api.cryptocompare.com/data/histoday?tsym=USD&aggregate=1&limit=365&api_key='
CC_URL = CC_URL_STEM + get_secret_data('CRYPTOCOMPARE_API_KEY') + '&fsym=' # + BTC


def build_cache_from_coincompare():
    bucket = get_crypto_bucket()
    coi_blob = bucket.blob('coins_of_interest.json')
    coins_list = json.loads(coi_blob.download_as_string())
    for symbol in coins_list:
        symbol = symbol.upper()
        sym_data_obj = get_data_for_symbol(symbol)
        sym_blob = bucket.blob('history/' + symbol + '.json')
        sym_blob.upload_from_string(json.dumps(sym_data_obj, indent=4))
        time.sleep(0.1) # Chill, don't overload their API endpoint
        break


def get_data_for_symbol(symbol):
    response = requests.get(CC_URL + symbol, headers={"Accept":"application/json"})
    data = response.text
    days_list = json.loads(data)['Data']
    price_dict = {}
    for day in days_list:
        ts:int = day['time']
        price:int = day['close']
        price_dict[ts] = price
    
    ts_list = list(price_dict.keys())
    ts_list.sort()
    price_list = [price_dict[ts] for ts in ts_list]
    return price_list