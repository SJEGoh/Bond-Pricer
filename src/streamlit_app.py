import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from urllib.parse import quote_plus
from helper import query_bonds, query_facets


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
        currency = bond_type = coupon_type = None
        perp = issuer_call = holder_put = None

        base_facets = query_facets(conn)

        with col1:
            currency = st.selectbox("Currency", 
                                    [x for x in (base_facets["currencies"] or []) if x], 
                                    index = None,
                                    placeholder = "Select a Currency")

            bond_type = st.selectbox("Bond Type",
                                    [x for x in (base_facets["bond_types"] or []) if x],
                                    index = None,
                                    placeholder = "Bond Type")
            bond_rating = st.selectbox("Fitch Bond Rating",
                                    [x for x in (base_facets["bond_ratings"] or []) if x],
                                    index = None,
                                    placeholder = "Bond Rating")
        with col2:

            coupon_type = st.selectbox("Coupon Type",
                                    [x for x in (base_facets["coupon_types"] or []) if x],
                                    index = None,
                                    placeholder = "Coupon Type")
            
            perp = st.selectbox("Perpetual Bond", 
                                ["Yes", "No"],
                                index = None,
                                placeholder = "Perpetual")
            st.text_input("Loan Tenure (Years)",
                          value = 0.00,
                          )
        with col3:
            issuer_call = st.selectbox("Issuer Right to Call", 
                                ["Yes", "No"],
                                index = None,
                                placeholder = "Issuer Call")
            
            holder_put = st.selectbox("Holder Right to Put", 
                                ["Yes", "No"],
                                index = None,
                                placeholder = "Holder Put")
            st.text_input("Loan Interest (%)",
                          value = 0.00,
                          )
        filters = dict(
            bond_rating = bond_rating,
            currency = currency,
            bond_type = bond_type,
            coupon_type = coupon_type,
            perpetual = perp[0] if perp else None,
            issuer_call = issuer_call[0] if issuer_call else None,
            holder_put = holder_put[0] if holder_put else None,
        )

        maturity_facets = query_facets(engine, exclude  = ["maturity_date"], **filters)
        ytw_facets = query_facets(engine, exclude = ["offer_ytw"], **filters)

        maturity_min = maturity_facets["mat_min"]
        maturity_max = maturity_facets["mat_max"]
        maturity_min = maturity_min.to_pydatetime() if pd.notna(maturity_min) else None
        maturity_max = maturity_max.to_pydatetime() if pd.notna(maturity_max) else None

        mat_min, mat_max = st.slider("Maturity Date",
                            maturity_min,
                            maturity_max,
                            (maturity_min, maturity_max)
                            )
        
        _ytw_min = ytw_facets["ytw_min"]
        _ytw_max = ytw_facets["ytw_max"]
        ytw_min, ytw_max = st.slider("Yielf to Worst (%)",
                              _ytw_min,
                              _ytw_max,
                              (_ytw_min, _ytw_max),
                              step = 0.01)
        filters["maturity_min"] = mat_min
        filters["maturity_max"] = mat_max
        filters["ytw_min"] = ytw_min
        filters["ytw_max"] = ytw_max
        df = query_bonds(engine, **filters)
        st.dataframe(df)
    print("update")
if __name__ == "__main__":
    main()


