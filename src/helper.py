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
        dic = pd.DataFrame([d["bondInfo"]])[["bondName", "issueCode", "offer_YTM", "offer_YldToWorst", 
                                         "bondCurrencyCode", "couponRate","couponFrequency", 
                                         "bidPrice", "offerPrice", "issuerCall", "holderPut", 
                                         "nextCallDate", "maturityDate", "yearsToMaturity","perpetual", 
                                         "issuerFitchRating", "bondSnpRating", "status", "bondType", 
                                         "couponType"]]
        dic.columns = ["bond_name", "issue_code", "offer_ytm", "offer_ytw",
                       "bond_currency_code", "coupon_rate", "coupon_frequency",
                       "bid_price", "offer_price", "issuer_call", "holder_put", 
                       "next_call_date", "maturity_date", "years_to_maturity","perpetual",
                       "fitch_rating", "snp_rating", "status", "bond_type", "coupon_type"]
        empt = pd.concat([empt, dic])
    empt["maturity_date"] = pd.to_datetime(empt["maturity_date"], unit="ms")
    empt["next_call_date"] = pd.to_datetime(empt["next_call_date"], unit="ms", errors="coerce")

    return empt.reset_index(drop = True)

def get_unique(_conn, _column):
    unique_currency = text(
        f"""
            SELECT DISTINCT {_column} FROM public.bonds;
        """
    )

    return list(pd.read_sql(unique_currency, _conn)[_column])


def get_edge(_conn, _column):
    min_max = text(
        f"""
            SELECT 
            MIN({_column}) AS min,
            MAX({_column}) AS max
            FROM public.bonds;
        """
    )
    df = pd.read_sql(min_max, _conn)
    return df["min"].iloc[0], df["max"].iloc[0]


from sqlalchemy import text
import pandas as pd

def query_bonds(engine, currency, y_min, y_max, t_min, t_max):
    where_clauses = [
        "offer_ytw BETWEEN :ymin AND :ymax",
        "maturity_date BETWEEN :tmin AND :tmax"
    ]

    params = {
        "ymin": float(y_min),
        "ymax": float(y_max),
        "tmin": t_min,
        "tmax": t_max,
    }

    if currency:
        where_clauses.append("bond_currency_code = :ccy")
        params["ccy"] = currency

    where_sql = " AND ".join(where_clauses)

    q = text(f"""
        SELECT
            issue_code,
            offer_ytw,
            coupon_rate,
            maturity_date
        FROM public.bonds
        WHERE {where_sql}
        ORDER BY offer_ytw DESC
        LIMIT 200;
    """)

    return pd.read_sql(q, engine, params=params)
