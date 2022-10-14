import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from google.cloud import storage, secretmanager
import json
import time
from charset_normalizer import detect
from secrets import get_secret_data

response_headers = {
    'Content-Type': 'application/xml'
}

def get_materialized_body(url: str):
    response = requests.get(url, headers={"User-Agent":"RSS Feed Reader"})
    data = response.text
    rootEL = ET.fromstring(data)
    rootEL.set("xmlns:content","http://purl.org/rss/1.0/modules/content/")
    
    ttlEL = ET.Element('ttl')
    ttlEL.text = '60' # Seconds
    channelEL = rootEL.find('channel')
    channelEL.append(ttlEL)

    storage_client = storage.Client()
    bucket = storage_client.bucket(get_secret_data('CMC_BUCKET_NAME'))
    articles_blob = bucket.blob('rss_articles.json')
    
    # Prepping all time high dictionary
    is_articles_dict_stale = False
    articles_dict = {}
    if articles_blob.exists():
        articles_dict = json.loads(articles_blob.download_as_string())

    http_request_count = 0
    for itemEL in channelEL.findall('item'):
        itemURL = itemEL.find('link').text
        articleStr = None
        if itemURL in articles_dict:
            articleStr = articles_dict[itemURL]
        else:
            http_request_count += 1
            print("Making request to url -> " + itemURL)
            itemResponse = requests.get(itemURL, headers={"User-Agent":"RSS Feed Reader"})
            itemPage = itemResponse.text
            soup = BeautifulSoup(itemPage, 'html.parser', from_encoding="utf-8")
            article = soup.find('article')
            articleStr = str(article)
            articles_dict[itemURL] = articleStr
            is_articles_dict_stale = True
            time.sleep(0.5)
            print(articleStr)
        contentEL = ET.Element('content:encoded')
        contentEL.text = "<![CDATA[ " + articleStr + " ]]>"
        itemEL.append(contentEL)
        if http_request_count > 10:
            break
    
    if is_articles_dict_stale:
        articles_blob.upload_from_string(json.dumps(articles_dict, indent=4))

    modified_data = ET.tostring(rootEL, encoding='utf-8') #.decode('utf8')
    return (modified_data, 200, response_headers)
