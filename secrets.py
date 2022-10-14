from google.cloud import storage, secretmanager
import os

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')

def get_secret_data(key):
    client = secretmanager.SecretManagerServiceClient()
    secret_detail = 'projects/' + PROJECT_ID + '/secrets/' + key + '/versions/latest' 
    response = client.access_secret_version(request={"name": secret_detail})
    data = response.payload.data.decode("UTF-8")
    # print("Data: {}".format(data))
    return data
