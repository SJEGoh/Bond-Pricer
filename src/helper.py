import requests
import pandas as pd

def get_bond_data():
    url = "https://www.bondsupermart.com/main/ws/v3/bond-selector/filter"   # your endpoint
    payload = {"orderBy":"bondIssuer","order":"asc","pageSize":"25","locale":"en-us"}  # exactly what you saw under "Request Payload"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.bondsupermart.com",
        "Referer": "https://www.bondsupermart.com/main/....",
        "User-Agent": "Mozilla/5.0",
    }
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    l = r.json()["bondList"]
    empt = pd.DataFrame()
    for d in l:
        dic = pd.DataFrame([d["bondInfo"]])[["issueCode", "offer_YTM", "offer_YldToWorst", 
                                         "bondCurrencyCode", "couponRate","couponFrequency", 
                                         "bidPrice", "offerPrice", "issuerCall", "holderPut", 
                                         "nextCallDate", "maturityDate", "perpetual", 
                                         "issuerFitchRating", "bondSnpRating", "status"]]
        empt = pd.concat([empt, dic])
    empt["maturityDate"] = pd.to_datetime(empt["maturityDate"], unit="ms")
    empt["nextCallDate"] = pd.to_datetime(empt["nextCallDate"], unit="ms", errors="coerce")

    return empt.reset_index(drop = True)
