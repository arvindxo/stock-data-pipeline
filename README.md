# 📈 Stock Market Data Pipeline

An end-to-end data engineering pipeline that ingests real stock market data,
processes it using PySpark on AWS Glue, and serves analytics via AWS Athena
and a Streamlit dashboard.

## 🏗️ Architecture
<!-- Add architecture diagram here later -->

## 🛠️ Tech Stack
- **Cloud:** AWS S3, Glue, Lambda, Athena, CloudWatch, IAM
- **Processing:** PySpark (AWS Glue)
- **Ingestion:** Python, yfinance, boto3
- **Visualization:** Streamlit, Plotly
- **Orchestration:** AWS Lambda + EventBridge

## 📁 Project Structure
\`\`\`
  stock-data-pipeline/
  ├── ingestion/         # Lambda ingestion script
  ├── transformation/    # PySpark Glue jobs
  ├── sql/               # Athena queries
  ├── dashboard/         # Streamlit app
  ├── infrastructure/    # Setup notes & config
  └── data/sample/       # Sample data for local testing
\`\`\`

## 🚀 How to Run Locally
<!-- To be filled in -->

## 📊 Dashboard
<!-- Add screenshot + Streamlit link later -->
