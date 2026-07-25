import yfinance as yf
import pandas as pd
import boto3
import pyarrow as pa
import pyarrow.parquet as pq
import os
import io
from datetime import datetime
from dotenv import load_dotenv


load_dotenv(".env.example")

# ---------- Config ----------
TICKERS = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA", "NFLX", "AMZN", "JPM"]
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
START_DATE = "2022-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

# ---------- S3 Client ----------
print("S3_BUCKET =", S3_BUCKET)
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

def fetch_stock_data(ticker: str) -> pd.DataFrame:
    """Fetch OHLCV data for a ticker using yfinance."""
    print(f"Fetching data for {ticker}...")
    df = yf.download(ticker, start=START_DATE, end=END_DATE, auto_adjust=True)
    
    # Fix for yfinance MultiIndex columns: ('Close', 'AAPL') -> 'close'
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0].lower() for col in df.columns]
    else:
        df.columns = [col.lower() for col in df.columns]
    
    df.reset_index(inplace=True)
    df.rename(columns={"Date": "date", "Price": "date"}, inplace=True)
    df["ticker"] = ticker
    df["year"] = pd.to_datetime(df["date"]).dt.year
    df["month"] = pd.to_datetime(df["date"]).dt.month
    df["date"] = df["date"].astype(str)
    return df

def upload_to_s3(df: pd.DataFrame, ticker: str):
    """Upload DataFrame as Parquet to S3 raw zone."""
    table = pa.Table.from_pandas(df)
    buffer = io.BytesIO()
    pq.write_table(table, buffer)
    buffer.seek(0)

    # Partitioned path: raw/stocks/ticker=AAPL/data.parquet
    s3_key = f"raw/stocks/ticker={ticker}/data.parquet"

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=buffer.getvalue()
    )
    print(f"  ✅ Uploaded to s3://{S3_BUCKET}/{s3_key}")

def main():
    print(f"=== Stock Ingestion Started: {END_DATE} ===\n")
    for ticker in TICKERS:
        try:
            df = fetch_stock_data(ticker)
            if df.empty:
                print(f"  ⚠️ No data for {ticker}, skipping.")
                continue
            upload_to_s3(df, ticker)
        except Exception as e:
            print(f"\nError processing {ticker}")
            traceback.print_exc()
    print("\n=== Ingestion Complete ===")

if __name__ == "__main__":
    main()