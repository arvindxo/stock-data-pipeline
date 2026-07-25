# 📈 Stock Market Data Pipeline

An end-to-end data engineering pipeline that ingests real stock market data,
processes it with PySpark on AWS Glue using the Medallion Architecture,
and serves interactive analytics via a Streamlit dashboard.

🔗 **[Live Dashboard](https://stock-data-pipeline-fshwb64anrgokrsnwag6pd.streamlit.app/)**

---

## 🏗️ Architecture
[Yahoo Finance API]
↓
AWS Lambda (Daily Trigger)
↓
S3 Raw Zone (Bronze)
↓
AWS Glue + PySpark (Silver Job)
→ Clean, deduplicate, add daily_return, price_range
↓
S3 Processed Zone (Silver)
↓
AWS Glue + PySpark (Gold Job)
→ Moving averages, volatility, monthly aggregates
↓
S3 Curated Zone (Gold)
↓
AWS Glue Crawler → Glue Data Catalog
↓
AWS Athena (SQL Analytics)
↓
Streamlit Dashboard (Live)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Cloud | AWS S3, Glue, Athena, Lambda, CloudWatch, IAM |
| Processing | PySpark (AWS Glue 4.0) |
| Ingestion | Python, yfinance, boto3 |
| Visualization | Streamlit, Plotly |
| Language | Python 3.x |
| Storage Format | Apache Parquet |

---

## 📁 Project Structure
stock-data-pipeline/
├── ingestion/
│ └── lambda_ingest.py # Pulls OHLCV data from Yahoo Finance → S3
├── transformation/
│ ├── glue_job_silver.py # PySpark: clean & enrich raw data
│ └── glue_job_gold.py # PySpark: moving averages, volatility, aggregates
├── sql/
│ └── athena_queries.sql # Analytics queries on gold layer
├── dashboard/
│ └── app.py # Streamlit dashboard
├── infrastructure/
│ └── setup_notes.md # AWS setup reference
├── .env.example # Environment variable template
└── requirements.txt

---

## 📊 Dashboard Features

- 📌 **KPI Cards** — Latest price and daily return per ticker
- 🕯️ **Candlestick Chart** — OHLCV with 7-day and 30-day moving averages
- 📉 **Daily Returns** — Multi-ticker return comparison over time
- ⚡ **Volatility Chart** — 30-day rolling volatility per ticker
- 🗓️ **Monthly Heatmap** — Monthly return heatmap (green = positive, red = negative)
- 🚦 **MA Crossover Signals** — Bullish/Bearish signals based on MA crossover

---

## 🗄️ Medallion Architecture

| Layer | Zone | Description |
|---|---|---|
| Bronze | `s3://bucket/raw/` | Raw OHLCV parquet files as ingested |
| Silver | `s3://bucket/processed/` | Cleaned, typed, enriched with daily return & price range |
| Gold | `s3://bucket/curated/` | Moving averages, volatility scores, monthly aggregates |

---

## 📈 Tickers Tracked

`AAPL` `GOOGL` `MSFT` `TSLA` `AMZN` `META` `NVDA` `NFLX` `JPM`

---

## 🚀 How to Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/arvindxo/stock-data-pipeline.git
cd stock-data-pipeline
```

### 2. Create virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Fill in your real AWS credentials in .env
```

### 5. Run ingestion
```bash
python ingestion/lambda_ingest.py
```

### 6. Run dashboard
```bash
streamlit run dashboard/app.py
```

---

## ☁️ AWS Setup

| Service | Purpose | Free Tier |
|---|---|---|
| S3 | Data Lake (Bronze/Silver/Gold) | 5GB free |
| Glue | PySpark ETL jobs | 10 DPU-hours/month |
| Athena | SQL analytics on S3 | 1TB queries/month |
| Lambda | Scheduled ingestion trigger | 1M requests/month |
| CloudWatch | Logging & monitoring | Always free |

---

## 🔑 Key Concepts Demonstrated

- **Medallion Architecture** (Bronze → Silver → Gold)
- **Partitioned Parquet** on S3 for efficient querying
- **PySpark Window Functions** for moving averages and lag calculations
- **AWS Glue Data Catalog** for schema management
- **Serverless SQL** via Athena
- **Secrets management** with `.env` and Streamlit secrets

---

## 📸 Screenshots

<!-- Add screenshots of your dashboard here -->

---

## 👤 Author

**Arvind** — [GitHub](https://github.com/arvindxo)