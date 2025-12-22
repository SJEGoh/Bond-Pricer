import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv
from urllib.parse import quote_plus
from helper import query_bonds, query_facets, get_graph_df, make_plot, get_bond_data
import plotly.graph_objects as go



load_dotenv()

user = os.getenv("DB_USER")
password = quote_plus(os.getenv("DB_PASSWORD"))  # URL-safe
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db = os.getenv("DB_NAME")
engine = create_engine(
    f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
)

with engine.connect() as conn:
    print("SQL Database Connected")

def data_to_sql():
    df = get_bond_data()
    df.to_sql(
        name="bonds",
        con=engine,
        if_exists="replace",  
        index=False,
        method="multi",     
        chunksize=5000
    )

    print("Data Uploaded")

@st.cache_data
def get_bond_df():
    return data_to_sql()

get_bond_df()

def main():
    st.title("Interest Rate Arbitrage Calculator")
    st.set_page_config(page_title="Interest Rate Arbitrage Calculator", layout="wide")

    with engine.connect() as conn:
        currency = bond_type = coupon_type = None
        perpetual = issuer_call = holder_put = None

        base_facets = query_facets(conn)

        with st.sidebar:
            st.header("Filters")
            currency = st.selectbox("Currency", 
                                    [x for x in (base_facets["currencies"] or []) if x], 
                                    index = None,
                                    placeholder = "Select a Currency")

            bond_type = st.selectbox("Bond Type",
                                    [x for x in (base_facets["bond_types"] or []) if x],
                                    index = None,
                                    placeholder = "Bond Type")
            fitch_rating = st.selectbox("Fitch Issuer Rating",
                                    [x for x in (base_facets["fitch_ratings"] or []) if x],
                                    index = None,
                                    placeholder = "Fitch Issuer Rating")
            fitch_bond_rating = st.selectbox("Fitch Bond Rating",
                                    [x for x in (base_facets["fitch_bond_ratings"] or []) if x],
                                    index = None,
                                    placeholder = "Fitch Bond Rating")

            coupon_type = st.selectbox("Coupon Type",
                                    [x for x in (base_facets["coupon_types"] or []) if x],
                                    index = None,
                                    placeholder = "Coupon Type")
            
            perpetual = st.selectbox("Perpetual Bond", 
                                ["Yes", "No"],
                                index = None,
                                placeholder = "Perpetual")
            issuer_call = st.selectbox("Issuer Right to Call", 
                                ["Yes", "No"],
                                index = None,
                                placeholder = "Issuer Call")
            
            holder_put = st.selectbox("Holder Right to Put", 
                                ["Yes", "No"],
                                index = None,
                                placeholder = "Holder Put")
            interest = st.text_input("Loan Interest (%)",
                          value = 0.00,
                          )
        filters = dict(
            fitch_bond_rating = fitch_bond_rating,
            fitch_rating = fitch_rating,
            currency = currency,
            bond_type = bond_type,
            coupon_type = coupon_type,
            perpetual = perpetual[0] if perpetual else None,
            issuer_call = issuer_call[0] if issuer_call else None,
            holder_put = holder_put[0] if holder_put else None,
        )

        maturity_facets = query_facets(engine, exclude  = ["maturity_date"], **filters)
        ytw_facets = query_facets(engine, exclude = ["offer_ytw"], **filters)

        maturity_min = maturity_facets["mat_min"]
        maturity_max = maturity_facets["mat_max"]
        maturity_min = maturity_min.to_pydatetime() if pd.notna(maturity_min) else None
        maturity_max = maturity_max.to_pydatetime() if pd.notna(maturity_max) else None
        _ytw_min = ytw_facets["ytw_min"]
        _ytw_max = ytw_facets["ytw_max"]
        with st.expander("Advanced"):
            try:
                mat_min, mat_max = st.slider("Maturity Date",
                            maturity_min,
                            maturity_max,
                            (maturity_min, maturity_max)
                            )
            except:
                mat_min = 0
                mat_max = 0
            try:
                ytw_min, ytw_max = st.slider("Yielf to Worst (%)",
                              _ytw_min,
                              _ytw_max,
                              (_ytw_min, _ytw_max),
                              step = 0.01)
            except:
                ytw_min = 0
                ytw_max = 0
        filters["maturity_min"] = mat_min
        filters["maturity_max"] = mat_max
        filters["ytw_min"] = ytw_min
        filters["ytw_max"] = ytw_max
        df = query_bonds(engine, **filters)
        event = st.dataframe(df,
                     hide_index = True,
                     selection_mode = "single-row",
                     on_select = "rerun")
        rows = event.selection["rows"]
        fig = go.Figure()
        fig.update_xaxes(showspikes=True, spikecolor="green", spikesnap="cursor", spikemode="across")
        fig.update_layout(spikedistance=1000, hoverdistance=100)
        fig.update_layout(
            title="Net Arbitrage Cash Flows",
            xaxis_title="Year",
            yaxis_title="Cumulative Cash Flow"
        )
        if rows:
            i = rows[0]
            cf_df = get_graph_df(df.iloc[i].to_dict(), interest, engine)
            make_plot(fig, cf_df)
        st.plotly_chart(fig, width="stretch")

    print("update")

if __name__ == "__main__":
    main()


