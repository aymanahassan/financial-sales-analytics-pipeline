"""Print the three business answers from a completed local Spark output."""
import argparse
from pyspark.sql import SparkSession, functions as F

p = argparse.ArgumentParser()
p.add_argument('--input', default='data/processed/monthly_sales')
a = p.parse_args()
spark = SparkSession.builder.appName('FSAP-InspectResults').getOrCreate()
try:
    df = spark.read.parquet(a.input)
    print('1. Sales by month (GBP)')
    df.groupBy('sale_month').agg(F.round(F.sum('total_sales'), 2).alias('sales_gbp')).orderBy('sale_month').show(100, False)
    print('2. Countries by sales (GBP)')
    df.groupBy('country').agg(F.round(F.sum('total_sales'), 2).alias('sales_gbp'), F.round(F.sum('total_profit'), 2).alias('profit_gbp')).orderBy(F.desc('sales_gbp')).show(100, False)
    print('3. Monthly profit and margin')
    sums = df.groupBy('sale_month').agg(F.sum('total_sales').alias('sales'), F.sum('total_profit').alias('profit'))
    sums.select('sale_month', F.round('profit', 2).alias('profit_gbp'), F.when(F.col('sales') != 0, F.round(F.col('profit') / F.col('sales') * 100, 2)).alias('profit_margin_pct')).orderBy('sale_month').show(100, False)
finally:
    spark.stop()
