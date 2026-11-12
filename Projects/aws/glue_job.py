"""AWS Glue Spark job for financial sales CSV.
Upload financial_pipeline.py to S3 and supply --extra-py-files s3://.../financial_pipeline.py.
Glue arguments: --JOB_NAME --RAW_PATH --CURATED_PATH --QUARANTINE_PATH --SUPERSEDED_PATH --AGGREGATE_PATH
"""
import sys,json
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from financial_pipeline import SCHEMA,classify,aggregate,reconcile

args=getResolvedOptions(sys.argv,['JOB_NAME','RAW_PATH','CURATED_PATH','QUARANTINE_PATH','SUPERSEDED_PATH','AGGREGATE_PATH'])
sc=SparkContext.getOrCreate();glue=GlueContext(sc);spark=glue.spark_session
job=Job(glue);job.init(args['JOB_NAME'],args)
raw=spark.read.option('header',True).schema(SCHEMA).csv(args['RAW_PATH'])
curated,quarantine,superseded=classify(raw)
counts=reconcile(raw,curated,quarantine,superseded)
curated.write.mode('overwrite').partitionBy('country').parquet(args['CURATED_PATH'])
aggregate(curated).write.mode('overwrite').parquet(args['AGGREGATE_PATH'])
quarantine.write.mode('overwrite').json(args['QUARANTINE_PATH'])
superseded.write.mode('overwrite').json(args['SUPERSEDED_PATH'])
print('FINANCIAL_PIPELINE_RECONCILIATION '+json.dumps(counts,sort_keys=True))
job.commit()
