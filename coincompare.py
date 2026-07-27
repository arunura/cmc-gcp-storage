from google.cloud import storage
from common import get_secret_data, get_crypto_bucket
import json

# The 365-day historic data API from CryptoCompare is no longer functional/available.
# The constants and functions below are commented out and kept for reference/fallback purposes only.
# CC_URL_STEM = 'https://min-api.cryptocompare.com/data/histoday?tsym=USD&aggregate=1&limit=365&api_key='
# CC_URL = CC_URL_STEM + get_secret_data('CRYPTOCOMPARE_API_KEY') + '&fsym=' # + BTC


def build_cache_from_coincompare():
    bucket = get_crypto_bucket()
    
    # Load latest prices from marketdata.json
    marketdata_blob = bucket.blob('marketdata.json')
    if not marketdata_blob.exists():
        print("marketdata.json does not exist in GCS.")
        raise Exception("marketdata.json not found")
        
    market_data = json.loads(marketdata_blob.download_as_string())
    price_map = {}
    for coin in market_data:
        if 'symbol' in coin and 'current_price' in coin:
            price_map[coin['symbol'].upper()] = coin['current_price']

    # Load the list of coins of interest
    coi_blob = bucket.blob('coins_of_interest.json')
    if not coi_blob.exists():
        print("coins_of_interest.json does not exist in GCS.")
        raise Exception("coins_of_interest.json not found")
        
    coins_list = json.loads(coi_blob.download_as_string())
    
    # Update history for each coin
    for symbol in coins_list:
        symbol = symbol.upper()
        if symbol not in price_map:
            print(f"Warning: No current price data found in marketdata.json for symbol: {symbol}")
            continue
            
        current_price = price_map[symbol]
        sym_blob = bucket.blob('history/' + symbol + '.json')
        
        # Load previous history if it exists
        history = []
        if sym_blob.exists():
            try:
                history = json.loads(sym_blob.download_as_string())
                if not isinstance(history, list):
                    print(f"Warning: History for {symbol} is not a list. Resetting.")
                    history = []
            except Exception as e:
                print(f"Error loading history for {symbol}: {e}. Resetting.")
                history = []
        
        # Append latest price
        history.append(current_price)
        
        # Keep maximum 365 days of history
        if len(history) > 365:
            history.pop(0)
            
        # Upload updated history
        sym_blob.upload_from_string(json.dumps(history, indent=4), content_type='application/json')
        print(f"Updated history for {symbol} with price {current_price} (length: {len(history)})")


# def get_data_for_symbol(symbol):
#     print("Processing historic data build for symbol: " + symbol)
#     response = requests.get(CC_URL + symbol, headers={"Accept":"application/json"})
#     data = response.text
#     days_list = json.loads(data)['Data']
#     price_dict = {}
#     for day in days_list:
#         ts:int = day['time']
#         price:int = day['close']
#         price_dict[ts] = price
#     
#     ts_list = list(price_dict.keys())
#     ts_list.sort()
#     price_list = [price_dict[ts] for ts in ts_list]
#     return price_list