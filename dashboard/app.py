import streamlit as st
import pandas as pd
import boto3
import pyarrow.parquet as pq
import io
import os
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv

load_dotenv(".env.example")

# ---------- Page Config ----------
st.set_page_config(
    page_title="Stock Market Analytics",
    page_icon="📈",
    layout="wide"
)

# ---------- S3 Config ----------
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

@st.cache_resource
def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

@st.cache_data(ttl=3600)
def load_parquet_from_s3(prefix: str) -> pd.DataFrame:
    """Load all parquet files from an S3 prefix into a DataFrame."""
    s3 = get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)

    dfs = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".parquet"):
                response = s3.get_object(Bucket=S3_BUCKET, Key=key)
                buffer = io.BytesIO(response["Body"].read())
                df = pq.read_table(buffer).to_pandas()

                # Extract ticker from S3 path since partitioned column
                # may not be inside the file e.g. .../ticker=AAPL/...
                if "ticker" not in df.columns:
                    for part in key.split("/"):
                        if part.startswith("ticker="):
                            df["ticker"] = part.split("=")[1]
                            break

                dfs.append(df)

    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)
# ---------- Load Data ----------
@st.cache_data(ttl=3600)
def load_data():
    daily = load_parquet_from_s3("curated/aggregates/daily_enriched/")
    monthly = load_parquet_from_s3("curated/aggregates/monthly_aggregates/")
    daily["date"] = pd.to_datetime(daily["date"])
    return daily, monthly

# ---------- UI ----------
st.title("📈 Stock Market Analytics Dashboard")
st.markdown("End-to-end data pipeline powered by **AWS S3 · Glue · PySpark · Athena**")
st.divider()

with st.spinner("Loading data from S3..."):
    daily_df, monthly_df = load_data()

if daily_df.empty:
    st.error("No data found in S3. Please run the ingestion script first.")
    st.stop()

TICKERS = sorted(daily_df["ticker"].unique().tolist())

# ---------- Sidebar ----------
st.sidebar.title("⚙️ Filters")
selected_tickers = st.sidebar.multiselect(
    "Select Tickers", TICKERS, default=TICKERS[:3]
)
date_range = st.sidebar.date_input(
    "Date Range",
    value=[daily_df["date"].min(), daily_df["date"].max()]
)

if not selected_tickers:
    st.warning("Please select at least one ticker.")
    st.stop()

# Filter data
mask = (
    daily_df["ticker"].isin(selected_tickers) &
    (daily_df["date"] >= pd.to_datetime(date_range[0])) &
    (daily_df["date"] <= pd.to_datetime(date_range[1]))
)
filtered = daily_df[mask].sort_values("date")

# ---------- KPI Cards ----------
st.subheader("📊 Key Metrics")
cols = st.columns(len(selected_tickers))
for i, ticker in enumerate(selected_tickers):
    t_df = filtered[filtered["ticker"] == ticker]
    if t_df.empty:
        continue
    latest = t_df.iloc[-1]
    prev   = t_df.iloc[-2] if len(t_df) > 1 else latest
    delta  = latest["close"] - prev["close"]
    cols[i].metric(
        label=ticker,
        value=f"${latest['close']:.2f}",
        delta=f"{delta:.2f} ({latest['daily_return']*100:.2f}%)" if pd.notna(latest['daily_return']) else "N/A"
    )

st.divider()

# ---------- Candlestick Chart ----------
st.subheader("🕯️ Candlestick Chart with Moving Averages")
selected_single = st.selectbox("Select ticker for candlestick", selected_tickers)
candle_df = filtered[filtered["ticker"] == selected_single]

fig_candle = go.Figure()
fig_candle.add_trace(go.Candlestick(
    x=candle_df["date"],
    open=candle_df["open"],
    high=candle_df["high"],
    low=candle_df["low"],
    close=candle_df["close"],
    name=selected_single
))
fig_candle.add_trace(go.Scatter(
    x=candle_df["date"], y=candle_df["ma_7"],
    name="7-day MA", line=dict(color="orange", width=1.5)
))
fig_candle.add_trace(go.Scatter(
    x=candle_df["date"], y=candle_df["ma_30"],
    name="30-day MA", line=dict(color="blue", width=1.5)
))
fig_candle.update_layout(
    xaxis_rangeslider_visible=False,
    height=500,
    template="plotly_dark"
)
st.plotly_chart(fig_candle, use_container_width=True)

st.divider()

# ---------- Daily Returns Comparison ----------
st.subheader("📉 Daily Returns Comparison")
fig_returns = px.line(
    filtered,
    x="date", y="daily_return",
    color="ticker",
    title="Daily Returns Over Time",
    labels={"daily_return": "Daily Return", "date": "Date"},
    template="plotly_dark"
)
st.plotly_chart(fig_returns, use_container_width=True)

st.divider()

# ---------- Volatility Chart ----------
st.subheader("⚡ 30-Day Rolling Volatility")
fig_vol = px.line(
    filtered,
    x="date", y="volatility_30",
    color="ticker",
    title="30-Day Rolling Volatility",
    labels={"volatility_30": "Volatility", "date": "Date"},
    template="plotly_dark"
)
st.plotly_chart(fig_vol, use_container_width=True)

st.divider()

# ---------- Monthly Returns Heatmap ----------
st.subheader("🗓️ Monthly Returns Heatmap")
monthly_filtered = monthly_df[monthly_df["ticker"].isin(selected_tickers)].copy()
monthly_filtered["period"] = (
    monthly_filtered["year"].astype(str) + "-" +
    monthly_filtered["month"].astype(str).str.zfill(2)
)
pivot = monthly_filtered.pivot_table(
    index="ticker", columns="period",
    values="monthly_return"
)
fig_heat = px.imshow(
    pivot,
    color_continuous_scale="RdYlGn",
    title="Monthly Return Heatmap (Green = Positive, Red = Negative)",
    aspect="auto",
    template="plotly_dark"
)
st.plotly_chart(fig_heat, use_container_width=True)

st.divider()

# ---------- MA Crossover Signal ----------
st.subheader("🚦 Moving Average Crossover Signals")
signal_df = filtered.copy()
signal_df["signal"] = signal_df.apply(
    lambda r: "🟢 BULLISH" if r["ma_7"] > r["ma_30"]
    else ("🔴 BEARISH" if r["ma_7"] < r["ma_30"] else "🟡 NEUTRAL"),
    axis=1
)
latest_signals = signal_df.sort_values("date").groupby("ticker").last().reset_index()
st.dataframe(
    latest_signals[["ticker", "date", "close", "ma_7", "ma_30", "signal"]].round(2),
    use_container_width=True
)

st.divider()
st.caption("Built with ❤️ using AWS S3 · Glue · PySpark · Athena · Streamlit · Plotly")