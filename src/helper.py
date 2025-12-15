import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from urllib.parse import quote_plus
import requests

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
        dic.columns = ["issue_code", "offer_ytm", "offer_ytw",
                       "bond_currency_code", "coupon_rate", "coupon_frequency",
                       "bid_price", "offer_price", "issuer_call", "holder_put", 
                       "next_call_date", "maturity_date", "perpetual",
                       "fitch_rating", "snp_rating", "status"]
        empt = pd.concat([empt, dic])
    empt["maturityDate"] = pd.to_datetime(empt["maturity_date"], unit="ms")
    empt["nextCallDate"] = pd.to_datetime(empt["next_call_date"], unit="ms", errors="coerce")

    return empt.reset_index(drop = True)

@st.cache_data(ttl = 60)
def get_unique(_conn, _column):
    unique_currency = text(
        f"""
            SELECT DISTINCT {_column} FROM public.bonds;
        """
    )

    return list(pd.read_sql(unique_currency, _conn, params = {"_column": _column})[_column])


