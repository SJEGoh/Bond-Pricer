import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from urllib.parse import quote_plus
from helper import get_unique


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
    with engine.connect() as conn:
        unique_currency = get_unique(conn, "bond_currency_code")
        currency = st.selectbox("Currency", 
                                unique_currency, 
                                index = None,
                                placeholder = "Select a Currency")
        unique_bondtype = get_unique(conn, "")
        perp = st.selectbox("Perp", 
                            ["Yes", "No"],
                            index = None,
                            placeholder = "Perpetual")




if __name__ == "__main__":
    main()


