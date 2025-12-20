import pandas as pd
from sqlalchemy import text
import plotly.graph_objects as go

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

def query_bonds(engine, **filters):
    where_sql, params = build_bond_where(**filters)

    q = text(f"""
        SELECT
            bond_name,
            offer_price,
            offer_ytw,
            coupon_rate,
            maturity_date
        FROM public.bonds
        WHERE {where_sql}
        ORDER BY offer_ytw DESC
        LIMIT 200;
    """)
    try:
        df = pd.read_sql(q, engine, params=params)
    except:
        df = pd.DataFrame(columns = ["bond_name",
            "offer_price",
            "offer_ytw",
            "coupon_rate",
            "maturity_date"])

    df.columns = ["Bond Name", "Ask Price", "Yield-to-Worse", "Coupon Rate", "Maturity Date"]
    return df

def build_bond_where(
    currency=None, bond_type=None, coupon_type=None,
    perpetual=None, issuer_call=None, holder_put=None,
    ytw_min=None, ytw_max=None, maturity_min=None, maturity_max=None,
    snp_rating = None, fitch_rating = None, exclude=set()
):
    where_clauses = []
    params = {}

    if ytw_min is not None and ytw_max is not None and "offer_ytw" not in exclude:
        where_clauses.append("offer_ytw BETWEEN :ytw_min AND :ytw_max")
        params["ytw_min"] = float(ytw_min)
        params["ytw_max"] = float(ytw_max)

    if maturity_min is not None and maturity_max is not None and "maturity_date" not in exclude:
        where_clauses.append("maturity_date BETWEEN :maturity_min AND :maturity_max")
        params["maturity_min"] = maturity_min
        params["maturity_max"] = maturity_max

    if currency and "bond_currency_code" not in exclude:
        where_clauses.append("bond_currency_code = :ccy")
        params["ccy"] = currency

    if bond_type and "bond_type" not in exclude:
        where_clauses.append("bond_type = :bond_type")
        params["bond_type"] = bond_type

    if coupon_type and "coupon_type" not in exclude:
        where_clauses.append("coupon_type = :coupon_type")
        params["coupon_type"] = coupon_type

    if perpetual and "perpetual" not in exclude:
        where_clauses.append("perpetual = :perpetual")
        params["perpetual"] = perpetual[0] if isinstance(perpetual, (list, tuple)) else perpetual

    if issuer_call and "issuer_call" not in exclude:
        where_clauses.append("issuer_call = :issuer_call")
        params["issuer_call"] = issuer_call[0] if isinstance(issuer_call, (list, tuple)) else issuer_call

    if holder_put and "holder_put" not in exclude:
        where_clauses.append("holder_put = :holder_put")
        params["holder_put"] = holder_put[0] if isinstance(holder_put, (list, tuple)) else holder_put

    if fitch_rating and "fitch_rating" not in exclude:
        where_clauses.append("fitch_rating = :fitch_rating")
        params["fitch_rating"] = fitch_rating

    if snp_rating and "snp_rating" not in exclude:
        where_clauses.append("fitch_rating = :snp_rating")
        params["snp_rating"] = snp_rating

    where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"
    return where_sql, params

def query_facets(engine, exclude=set(), **filters):
    where_sql, params = build_bond_where(exclude=exclude, **filters)

    q = text(f"""
        SELECT
            array_agg(DISTINCT bond_currency_code) AS currencies,
            array_agg(DISTINCT bond_type) AS bond_types,
            array_agg(DISTINCT coupon_type) AS coupon_types,
            array_agg(DISTINCT fitch_rating) AS fitch_ratings,
            array_agg(DISTINCT snp_rating) AS snp_ratings,
            MIN(offer_ytw) AS ytw_min,
            MAX(offer_ytw) AS ytw_max,
            MIN(maturity_date) AS mat_min,
            MAX(maturity_date) AS mat_max
        FROM public.bonds
        WHERE {where_sql};
    """)
    return pd.read_sql(q, engine, params=params).iloc[0].to_dict()

def get_graph_df(bond, interest, engine):
    q = text(f"""
            SELECT
                coupon_frequency,
                years_to_maturity,
                next_call_date
             FROM public.bonds
             WHERE bond_name = '{bond["bond_name"]}';
             """)
    df = pd.read_sql(q, engine)

    years_mat = float(df["years_to_maturity"].iloc[0])
    coupon_freq = int(df["coupon_frequency"].iloc[0])
    total_periods = int(round(years_mat * coupon_freq))
    time_step = 1.0/coupon_freq

    today = pd.Timestamp.today()
    if df["next_call_date"].item():
        next_call = df["next_call_date"].iloc[0]
        years_left = (next_call - today).days / 365.25
    else:
        next_call = None

    units = 100/bond["offer_price"]
    coupon = units * bond["coupon_rate"]/(coupon_freq)

    time = [0]
    cf_loan = [100]
    last_ = 100
    cf_bond = [100]
    for t in range(1, total_periods):
        if t%coupon_freq == 0:
            cf_loan.append(last_ + float(interest))
            last_ = cf_loan[-1]
        else:
            cf_loan.append(last_)
        time.append(t * time_step)
        cf_bond.append(cf_bond[-1] + coupon)
    
    cf_df = pd.DataFrame({"time": time, "cf_loan": cf_loan, "cf_bond": cf_bond})
    return cf_df    

def make_plot(fig, cf_df):
    cf_df["cf_diff"] = cf_df["cf_bond"] - cf_df["cf_loan"]
    fig.add_trace(go.Scatter(x = cf_df["time"], y = cf_df["cf_bond"],
                             customdata=cf_df[["cf_loan", "cf_diff"]].to_numpy(),
                            hovertemplate=(
                                "<b>t</b>: %{x:.2f}<br>"
                                "<b>Bond CF</b>: %{y:.2f}<br>"
                                "<b>Loan CF</b>: %{customdata[0]:.2f}<br>"
                                "<b>CF Diff</b>: %{customdata[1]:.2f}"
                                "<extra></extra>"
                            )))
    fig.add_trace(go.Scatter(x = cf_df["time"], y = cf_df["cf_loan"]))
