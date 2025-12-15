import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from urllib.parse import quote_plus
from helper import get_unique, get_edge, query_bonds


load_dotenv()

user = os.getenv("DB_USER")
password = quote_plus(os.getenv("DB_PASSWORD"))  # URL-safe
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db = os.getenv("DB_NAME")
engine = create_engine(
    f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
)

def main():
    st.title("Interest Rate Arbitrage Calculator")
    col1, col2, col3 = st.columns(3)
    with engine.connect() as conn:
        with col1:
            unique_currency = get_unique(conn, "bond_currency_code")
            currency = st.selectbox("Currency", 
                                    unique_currency, 
                                    index = None,
                                    placeholder = "Select a Currency")
            unique_bond_type = get_unique(conn, "bond_type")
            bond_type = st.selectbox("Bond Type",
                                    unique_bond_type,
                                    index = None,
                                    placeholder = "Bond Type")
        with col2:
            unique_coupon_type = get_unique(conn, "coupon_type")
            coupon_type = st.selectbox("Coupon Type",
                                    unique_coupon_type,
                                    index = None,
                                    placeholder = "Coupon Type")
            perp = st.selectbox("Perpetual Bond", 
                                ["Yes", "No"],
                                index = None,
                                placeholder = "Perpetual")
        with col3:
            issuer_call = st.selectbox("Issuer Right to Call", 
                                ["Yes", "No"],
                                index = None,
                                placeholder = "Issuer Call")
            holder_put = st.selectbox("Holder Right to Put", 
                                ["Yes", "No"],
                                index = None,
                                placeholder = "Holder Put")
        maturity_min, maturity_max = get_edge(conn, "maturity_date")
        maturity_min = maturity_min.to_pydatetime() if pd.notna(maturity_min) else None
        maturity_max = maturity_max.to_pydatetime() if pd.notna(maturity_max) else None
        maturity_range = st.slider("Maturity Date",
                                   maturity_min,
                                   maturity_max,
                                   (maturity_min, maturity_max)
                                   )
        coupon_min, coupon_max = get_edge(conn, "coupon_rate")
        coupon_range = st.slider("Coupon Rate (%)",
                                 coupon_min,
                                 coupon_max,
                                 (coupon_min, coupon_max))
        ytw_min, ytw_max = get_edge(conn, "offer_ytw")
        ytw_range = st.slider("Yielf to Worst (%)",
                              -10.0,
                              10.0,
                              (-10.0, 10.0),
                              step = 0.01)

    df = query_bonds(engine, currency, ytw_min, ytw_max, maturity_min, maturity_max)
    st.dataframe(df)


if __name__ == "__main__":
    main()


