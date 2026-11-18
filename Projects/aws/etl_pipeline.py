"""AWS Glue ETL entry point for the Financial Sales Analytics Pipeline."""

import json
import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from financial_pipeline import SCHEMA, aggregate, classify, reconcile

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "RAW_PATH",
        "CURATED_PATH",
        "QUARANTINE_PATH",
        "SUPERSEDED_PATH",
        "AGGREGATE_PATH",
    ],
)

spark_context = SparkContext.getOrCreate()
glue_context = GlueContext(spark_context)
spark = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)


raw_df = (
    spark.read
    .option("header", True)
    .schema(SCHEMA)
    .csv(args["RAW_PATH"])
)

curated_df, quarantine_df, superseded_df = classify(raw_df)

reconciliation_counts = reconcile(
    raw_df,
    curated_df,
    quarantine_df,
    superseded_df,
)
curated_df.write.mode("overwrite").partitionBy("country").parquet(
    args["CURATED_PATH"]
)

monthly_sales_df = aggregate(curated_df)

monthly_sales_df.write.mode("overwrite").parquet(
    args["AGGREGATE_PATH"]
)

quarantine_df.write.mode("overwrite").json(
    args["QUARANTINE_PATH"]
)

superseded_df.write.mode("overwrite").json(
    args["SUPERSEDED_PATH"]
)

print(
    "FINANCIAL_PIPELINE_RECONCILIATION "
    + json.dumps(reconciliation_counts, sort_keys=True)
)

job.commit()
