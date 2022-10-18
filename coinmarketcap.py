from google.cloud import storage
from common import get_secret_data, get_crypto_bucket
import json
import requests

CMC_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?start=1&limit=1000&convert=USD'

def build_cache_from_cmc():
    bucket = get_crypto_bucket()
    ath_blob = bucket.blob('ath.json')
    
    # Prepping all time high dictionary
    is_ath_stale = False
    ath_dict = None
    if ath_blob.exists():
        ath_dict = json.loads(ath_blob.download_as_string())
    else:
        is_ath_stale = True
        ath_dict = json.load(open('ath_seed.json'))
    
    print("Building cache from cmc data")
    response = requests.get(CMC_URL, headers={"Accept":"application/json", "X-CMC_PRO_API_KEY": get_secret_data('CMC_API_KEY')})
    data = response.text
    coin_array = json.loads(data)['data']
    results_array = []
    for coinobj in coin_array:
        # Determine what's the ATH for this coin from historical and current prices.
        symbol_lwr = coinobj['symbol'].lower()
        current_price = coinobj['quote']['USD']['price']
        ath = None
        # If the current price is atleast 5% more than previous ATH, then set a new ATH. 
        # We use the 5% to avoid frequent writes for incremental price highs when the price is moving up.
        if symbol_lwr in ath_dict and (ath_dict[symbol_lwr]*1.05) > current_price: 
            ath = ath_dict[symbol_lwr]
        else:
            # current price is highest and we also need to record this in the ath.json
            print("New ATH set by coin -> " + symbol_lwr)
            ath = current_price
            ath_dict[symbol_lwr] = ath
            is_ath_stale = True
        # Now lets create the result object for this coin
        res_obj = {}
        res_obj['id'] = coinobj['slug']
        res_obj['name'] = coinobj['name']
        res_obj['symbol'] = coinobj['symbol']
        res_obj['current_price'] = current_price
        res_obj['market_cap'] = coinobj['quote']['USD']['market_cap']
        res_obj['market_cap_rank'] = coinobj['cmc_rank']
        res_obj['pct_ch_24h'] = coinobj['quote']['USD']['percent_change_24h']
        res_obj['ath_chg_pct'] = (current_price - ath)*100 / ath # Will always be a negative percentage
        res_obj['image'] = 'https://s2.coinmarketcap.com/static/img/coins/32x32/' + str(coinobj['id']) + '.png'
        res_obj['url'] = 'https://coinmarketcap.com/currencies/' + coinobj['slug'] + '/'
        res_obj['last_updated'] = coinobj['quote']['USD']['last_updated']
        results_array.append(res_obj)

    results_str = json.dumps(results_array, indent=4)
    # print(json.dumps(results_array))
    
    blob = bucket.blob('marketdata.json')
    blob.upload_from_string(results_str)
    blob.cache_control = 'no-store'
    blob.content_type = 'application/json'
    blob.patch()
    print('Results data uploaded to google cloud storage bucket')

    # upload new ath.json if needed
    if is_ath_stale:
        print('Uploaded new ath.json to GS')
        ath_blob.upload_from_string(json.dumps(ath_dict, indent=4))

    return len(results_array)