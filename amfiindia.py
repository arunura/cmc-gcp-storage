from common import get_crypto_bucket
import json
import requests

def build_cache_from_amfi():
    print("Fetching list of schemes of interest...")
    bucket = get_crypto_bucket()
    mf_of_interest_blob = bucket.blob('india_mf_of_interest.json')
    mf_of_int_str = mf_of_interest_blob.download_as_string()
    print(mf_of_int_str)
    in_scope = json.loads(mf_of_int_str)

    print("Building cache from amfi data...")
    response = requests.get("https://www.amfiindia.com/spages/NAVAll.txt")
    data = response.text
    lines = data.split("\n")
    results_array = []
    latest_fund_house = None
    for line in lines:
        # if line starts with number, then it's a valid line
        if line[0:5].isdigit():
            parts = line.split(";")
            scheme_code = int(parts[0])
            if scheme_code in in_scope:
                res_obj = {}
                res_obj['scheme_code'] = scheme_code
                res_obj['isin'] = parts[1]
                res_obj['scheme_name'] = parts[3]
                res_obj['net_asset_value'] = float(parts[4])
                res_obj['fund_house'] = latest_fund_house
                res_obj['date'] =  parts[5].strip()
                results_array.append(res_obj)
        elif len(line) > 5:
            latest_fund_house = line.strip()
    print("AMFI results parsed successfully with " + str(len(results_array)) + " records out of " + str(len(in_scope)) + " schemes of interest.")
    results_array.sort(key=lambda fund: fund['scheme_code'])
    results_str = json.dumps(results_array, indent=4)
    blob = bucket.blob('india_mf_nav.json')
    blob.upload_from_string(results_str)
    blob.cache_control = 'no-store'
    blob.content_type = 'application/json'
    blob.patch()
    print('Results data uploaded to google cloud storage bucket')
    return len(results_array)
