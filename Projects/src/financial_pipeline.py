"""Shared Spark financial sales ETL logic. No input data is embedded in this module."""
from pyspark.sql import Window, functions as F, types as T

SCHEMA = T.StructType([
    T.StructField('record_id', T.StringType()),
    T.StructField('source_row_id', T.StringType()),
    T.StructField('version', T.IntegerType()),
    T.StructField('ingested_at', T.StringType()),
    T.StructField('segment', T.StringType()),
    T.StructField('country', T.StringType()),
    T.StructField('product', T.StringType()),
    T.StructField('discount_band', T.StringType()),
    T.StructField('units_sold', T.DoubleType()),
    T.StructField('manufacturing_price', T.DoubleType()),
    T.StructField('sale_price', T.DoubleType()),
    T.StructField('gross_sales', T.DoubleType()),
    T.StructField('discounts', T.DoubleType()),
    T.StructField('sales', T.DoubleType()),
    T.StructField('cogs', T.DoubleType()),
    T.StructField('profit', T.DoubleType()),
    T.StructField('sale_date', T.StringType()),
    T.StructField('currency_code', T.StringType()),
])

REQUIRED = ['record_id','source_row_id','segment','country','product']

def classify(df):
    """Returns (curated, quarantine, superseded); each input row goes to exactly one."""
    typed = (df.withColumn('sale_day', F.to_date('sale_date', 'yyyy-MM-dd'))
             .withColumn('ingest_ts', F.to_timestamp('ingested_at', "yyyy-MM-dd'T'HH:mm:ss")))
    required_missing = F.lit(False)
    for col in REQUIRED:
        required_missing = required_missing | F.col(col).isNull() | (F.trim(F.col(col)) == '')
    invalid_numeric = (F.col('version').isNull() | (F.col('version') < 1) |
        F.col('units_sold').isNull() | (F.col('units_sold') <= 0) |
        F.col('manufacturing_price').isNull() | (F.col('manufacturing_price') < 0) |
        F.col('sale_price').isNull() | (F.col('sale_price') < 0) |
        F.col('gross_sales').isNull() | (F.col('gross_sales') < 0) |
        F.col('discounts').isNull() | (F.col('discounts') < 0) |
        F.col('sales').isNull() | (F.col('sales') < 0) |
        F.col('cogs').isNull() | (F.col('cogs') < 0) |
        F.col('profit').isNull())
    # A source row may legitimately be loss-making; profit can be negative.
    # Tolerance is absolute, allowing fractional units and decimal arithmetic.
    mismatch = ((F.abs(F.col('gross_sales') - F.col('units_sold')*F.col('sale_price')) > 0.05) |
        (F.abs(F.col('sales') - (F.col('gross_sales')-F.col('discounts'))) > 0.05) |
        (F.abs(F.col('profit') - (F.col('sales')-F.col('cogs'))) > 0.05))
    reason = (F.when(required_missing,'missing_identifier_or_dimension')
        .when(F.col('sale_day').isNull() | F.col('ingest_ts').isNull(), 'invalid_date')
        .when(F.col('currency_code').isNull() | (F.upper(F.trim(F.col('currency_code'))) != 'GBP'), 'unsupported_currency')
        .when(invalid_numeric, 'invalid_numeric')
        .when(mismatch, 'financial_reconciliation_failed'))
    marked = typed.withColumn('rejection_reason',reason)
    quarantine = marked.filter(F.col('rejection_reason').isNotNull())
    valid = marked.filter(F.col('rejection_reason').isNull())
    # record_id is synthetic and unique to a source row, NOT inferred from dimensions.
    win = Window.partitionBy('record_id').orderBy(F.col('version').desc(),F.col('ingest_ts').desc(),F.col('source_row_id').desc())
    ranked = valid.withColumn('_rank',F.row_number().over(win))
    curated = ranked.filter(F.col('_rank') == 1).drop('_rank','rejection_reason')
    superseded = ranked.filter(F.col('_rank') > 1).drop('_rank')
    return curated,quarantine,superseded

def aggregate(curated):
    return (curated.groupBy(F.date_format('sale_day','yyyy-MM').alias('sale_month'),'country','segment','product','currency_code')
        .agg(F.count('*').alias('record_count'),F.round(F.sum('sales'),2).alias('total_sales'),
             F.round(F.sum('profit'),2).alias('total_profit'),F.round(F.sum('units_sold'),2).alias('units_sold')))

def reconcile(raw,curated,quarantine,superseded):
    counts={'raw':raw.count(),'curated':curated.count(),'quarantined':quarantine.count(),'superseded':superseded.count()}
    counts['balanced']=counts['raw']==counts['curated']+counts['quarantined']+counts['superseded']
    if not counts['balanced']:raise RuntimeError(f'Reconciliation failed: {counts}')
    return counts
