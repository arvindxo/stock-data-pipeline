import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# ---------- Glue Job Init ----------
args = getResolvedOptions(sys.argv, ["JOB_NAME", "S3_BUCKET"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

S3_BUCKET = args["S3_BUCKET"]
SILVER_PATH = f"s3://{S3_BUCKET}/processed/stocks/"
GOLD_PATH   = f"s3://{S3_BUCKET}/curated/aggregates/"

# ---------- Read Silver Data ----------
print("Reading silver data...")
df = spark.read.parquet(SILVER_PATH)
print(f"Silver record count: {df.count()}")

# ---------- Window Specs ----------
window = Window.partitionBy("ticker").orderBy("date")
window_7  = window.rowsBetween(-6, 0)
window_30 = window.rowsBetween(-29, 0)

# ---------- Moving Averages ----------
print("Computing moving averages...")
df = df.withColumn("ma_7",  F.avg("close").over(window_7))
df = df.withColumn("ma_30", F.avg("close").over(window_30))

# ---------- Volatility (rolling std dev of daily return) ----------
print("Computing volatility...")
df = df.withColumn("volatility_7",  F.stddev("daily_return").over(window_7))
df = df.withColumn("volatility_30", F.stddev("daily_return").over(window_30))

# ---------- Monthly Aggregates ----------
print("Computing monthly aggregates...")
monthly = df.groupBy("ticker", "year", "month").agg(
    F.first("open").alias("monthly_open"),
    F.max("high").alias("monthly_high"),
    F.min("low").alias("monthly_low"),
    F.last("close").alias("monthly_close"),
    F.sum("volume").alias("monthly_volume"),
    F.avg("daily_return").alias("avg_daily_return"),
    F.stddev("daily_return").alias("monthly_volatility"),
    F.count("date").alias("trading_days")
)

monthly = monthly.withColumn(
    "monthly_return",
    (F.col("monthly_close") - F.col("monthly_open")) / F.col("monthly_open")
)

# ---------- Write Gold Zone ----------
print("Writing daily enriched data to Gold zone...")
df.write \
  .mode("overwrite") \
  .partitionBy("ticker") \
  .parquet(f"{GOLD_PATH}daily_enriched/")

print("Writing monthly aggregates to Gold zone...")
monthly.write \
  .mode("overwrite") \
  .partitionBy("ticker") \
  .parquet(f"{GOLD_PATH}monthly_aggregates/")

print(f"Gold layer written to {GOLD_PATH}")

job.commit()
print("=== Gold Job Complete ===")