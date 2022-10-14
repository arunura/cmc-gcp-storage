from flask import Flask
from flask import request
import requests
import json
from rssfeed import get_materialized_body
from google.cloud import storage
from secrets import get_secret_data

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

CMC_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?start=1&limit=1000&convert=USD'

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    #for k, v in os.environ.items():
    #    print(f'{k}={v}')
    return 'Hello World!'

@app.route('/rss/')
def get_rss():
    if 'feed' not in request.args:
        return "The feed parameter is missing. No action taken"
    feed = request.args.get('feed')
    if (not feed.startswith('http://')) and (not feed.startswith('https://')):
        feed = 'https://' + feed
    return get_materialized_body(feed)

@app.route('/cron')
def build_cache():
    storage_client = storage.Client()
    bucket = storage_client.bucket(get_secret_data('CMC_BUCKET_NAME'))
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

    return 'Cache build complete with ' + str(len(results_array)) + ' records.'

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. You
    # can configure startup instructions by adding `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
