"""Local batch pipeline: synthetic sales CSV -> curated/aggregated Parquet + JSON exceptions."""
import argparse,json
from pathlib import Path
from pyspark.sql import SparkSession
from financial_pipeline import SCHEMA,classify,aggregate,reconcile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',default='data/sales_events.csv')
    ap.add_argument('--output',default='data/processed')
    args=ap.parse_args()
    spark=SparkSession.builder.appName('FSAP-FinancialSalesETL').getOrCreate()
    try:
        raw=spark.read.option('header',True).schema(SCHEMA).csv(args.input)
        curated,quarantine,superseded=classify(raw)
        counts=reconcile(raw,curated,quarantine,superseded)
        out=Path(args.output)
        curated.write.mode('overwrite').partitionBy('country').parquet(str(out/'curated'))
        aggregate(curated).write.mode('overwrite').parquet(str(out/'monthly_sales'))
        quarantine.write.mode('overwrite').json(str(out/'quarantine'))
        superseded.write.mode('overwrite').json(str(out/'superseded'))
        out.mkdir(parents=True,exist_ok=True)
        (out/'run_summary.json').write_text(json.dumps(counts,indent=2)+'\n')
        print(json.dumps(counts,indent=2))
    finally:spark.stop()
if __name__=='__main__':main()
