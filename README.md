# CoinMarketCap to GCP Storage
This GCP App engine program gets market info from CoinMarketCap (on a schedule or on demand) and stores it to a GCP bucket, for access in other applications without going over the API limits.

## Requirements
1. CoinMarketCap API (Free version is sufficient for making a request every 30 mins).
2. GCP account and project setup, with **secrets manager** and **storage** APIs enabled.
3. Cloud console (or gcloud) for deploying the app.

## Setup
1. Store the Coinmarketcap API in secrets manager under the key `CMC_API_KEY`.
2. Create a bucket (or use an existing one) and store the bucket name in secrets manager under the key `CMC_BUCKET_NAME`.
3. Use `git clone` to get this code either on Cloud console or your local for gcloud.
4. Deploy the app using `gcloud app deploy`.
5. Setup the cron job using `gcloud app deploy cron.yaml` for automated data refresh on cloud storage.
6. Access the json data using `https://storage.googleapis.com/<BUCKET_NAME>/marketdata.json`

## Troubleshooting
To tail logs use `gcloud app logs tail`. Also, make sure to provide yout app engine service account the `Secret Manager Secret Accessor` role to be able to access the secrets.

