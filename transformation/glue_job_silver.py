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
RAW_PATH = f"s3://{S3_BUCKET}/raw/stocks/"
SILVER_PATH = f"s3://{S3_BUCKET}/processed/stocks/"

# ---------- Read Raw Data ----------
print("Reading raw data from S3...")
df = spark.read.parquet(RAW_PATH)

print(f"Raw record count: {df.count()}")
df.printSchema()

# ---------- Clean Data ----------
print("Cleaning data...")

# Drop nulls and duplicates
df = df.dropna(subset=["date", "close", "open", "high", "low", "volume"])
df = df.dropDuplicates(["ticker", "date"])

# Cast correct types
df = df.withColumn("date", F.to_date(F.col("date"), "yyyy-MM-dd")) \
       .withColumn("open",   F.col("open").cast("double")) \
       .withColumn("high",   F.col("high").cast("double")) \
       .withColumn("low",    F.col("low").cast("double")) \
       .withColumn("close",  F.col("close").cast("double")) \
       .withColumn("volume", F.col("volume").cast("long"))

# ---------- Add Derived Columns ----------
print("Adding derived columns...")

# Window spec: partition by ticker, order by date
window = Window.partitionBy("ticker").orderBy("date")

# Daily return: (close - prev_close) / prev_close
df = df.withColumn("prev_close", F.lag("close", 1).over(window))
df = df.withColumn(
    "daily_return",
    F.when(
        F.col("prev_close").isNotNull(),
        (F.col("close") - F.col("prev_close")) / F.col("prev_close")
    ).otherwise(None)
)

# Price range: high - low
df = df.withColumn("price_range", F.col("high") - F.col("low"))

# Day of week (Monday=1, Sunday=7)
df = df.withColumn("day_of_week", F.dayofweek(F.col("date")))

# Ingestion timestamp
df = df.withColumn("ingestion_timestamp", F.current_timestamp())

# Drop helper column
df = df.drop("prev_close")

# ---------- Write to Silver Zone ----------
print("Writing to Silver zone...")
df.write \
  .mode("overwrite") \
  .partitionBy("ticker", "year") \
  .parquet(SILVER_PATH)

print(f"Silver layer written to {SILVER_PATH}")
print(f"Silver record count: {df.count()}")

job.commit()
print("=== Silver Job Complete ===")