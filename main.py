from flask import Flask
from flask import request
from rssfeed import get_materialized_body
from coinmarketcap import build_cache_from_cmc

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)



@app.route('/')
def home():
    """Return a friendly HTTP greeting."""
    #for k, v in os.environ.items():
    #    print(f'{k}={v}')
    return '''
<!DOCTYPE html>
<html>
    <head>
        <title>Tools</title>
        <style>
        body {
        margin-left: 30px;
        }
        </style>
    </head>
    <body>
        <h2>Welcome to the tools page!</h2>
    </body>
</html>
    '''

@app.route('/rss/')
def get_rss():
    if 'feed' not in request.args:
        return "The feed parameter is missing. No action taken"
    feed = request.args.get('feed')
    if (not feed.startswith('http://')) and (not feed.startswith('https://')):
        feed = 'https://' + feed
    return get_materialized_body(feed)

@app.route('/cron_cmc')
def trigger_build_cache():
    res_count = build_cache_from_cmc()
    return 'Cache build complete with ' + str(res_count) + ' records.'

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. You
    # can configure startup instructions by adding `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
