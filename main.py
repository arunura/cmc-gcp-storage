from flask import Flask
import requests
import json
from google.cloud import storage, secretmanager
import os

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

CMC_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?start=1&limit=1000&convert=USD'
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')

def get_secret_data(key):
    client = secretmanager.SecretManagerServiceClient()
    secret_detail = 'projects/' + PROJECT_ID + '/secrets/' + key + '/versions/latest' 
    response = client.access_secret_version(request={"name": secret_detail})
    data = response.payload.data.decode("UTF-8")
    # print("Data: {}".format(data))
    return data

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    #for k, v in os.environ.items():
    #    print(f'{k}={v}')
    return 'Hello World!'

@app.route('/cron')
def build_cache():
    print("Building cache from cmc data")
    response = requests.get(CMC_URL, headers={"Accept":"application/json", "X-CMC_PRO_API_KEY": get_secret_data('CMC_API_KEY')})
    data = response.text
    coin_array = json.loads(data)['data']
    results_array = []
    for coinobj in coin_array:
        res_obj = {}
        res_obj['id'] = coinobj['slug']
        res_obj['name'] = coinobj['name']
        res_obj['symbol'] = coinobj['symbol']
        res_obj['current_price'] = coinobj['quote']['USD']['price']
        res_obj['market_cap'] = coinobj['quote']['USD']['market_cap']
        res_obj['market_cap_rank'] = coinobj['cmc_rank']
        res_obj['pct_ch_24h'] = coinobj['quote']['USD']['percent_change_24h']
        res_obj['ath_chg'] = ''
        res_obj['image'] = 'https://s2.coinmarketcap.com/static/img/coins/32x32/' + str(coinobj['id']) + '.png'
        res_obj['url'] = 'https://coinmarketcap.com/currencies/' + coinobj['slug'] + '/'
        res_obj['last_updated'] = coinobj['quote']['USD']['last_updated']
        results_array.append(res_obj)

    results_str = json.dumps(results_array, indent=4)
    print(json.dumps(results_array))
    storage_client = storage.Client()
    bucket = storage_client.bucket(get_secret_data('CMC_BUCKET_NAME'))
    blob = bucket.blob('marketdata.json')
    blob.upload_from_string(results_str)
    blob.cache_control = 'no-store'
    blob.content_type = 'application/json'
    blob.patch()
    print('Data uploaded to google cloud storage bucket')

    return 'Cache build complete with ' + str(len(results_array)) + ' records.'

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. You
    # can configure startup instructions by adding `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
