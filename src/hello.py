from helper import get_bond_data
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from urllib.parse import quote_plus

def main():
    load_dotenv()

    user = os.getenv("DB_USER")
    password = quote_plus(os.getenv("DB_PASSWORD"))  # URL-safe
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db = os.getenv("DB_NAME")

    df = get_bond_data()
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )

    with engine.connect() as conn:
        print("SQL Database Connected")

    df.to_sql(
        name="bonds",
        con=engine,
        if_exists="replace",  
        index=False,
        method="multi",     
        chunksize=5000
    )

    print("Data Uploaded")
    
    return 0

if __name__ == "__main__":
    main()


