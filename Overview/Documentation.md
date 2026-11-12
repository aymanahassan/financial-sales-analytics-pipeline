# Processing notes

## Source preparation

`prepare_source.py` reads the Financial Sample workbook and writes `data/source_sales.csv`. I use the sales, cost, discount, date, product, segment and country fields. The script adds a source-row reference and sets `currency_code` to GBP for this exercise.

`generate_events.py` uses the CSV to create repeatable test batches. It samples source rows using a fixed seed, assigns generated record IDs and adds a few deliberately invalid records and updated versions. This gives the Spark job something to reject or supersede instead of processing a completely clean file.

## PySpark

`financial_pipeline.py` contains the schema and transformations. `spark_job.py` runs the local batch and writes the results.

The main checks are missing IDs or dimensions, invalid dates, unsupported currency, numeric values and whether the amounts add up:

- Gross sales = units sold × sale price
- Sales = gross sales − discounts
- Profit = sales − COGS

I allow a tolerance of 0.05 for the amount comparisons. A negative profit is fine if the figures are consistent.

For generated records with the same `record_id`, the job keeps the latest valid version using version, ingestion timestamp and source-row reference as tie-breakers. Matching products or countries aren't treated as duplicates: the source doesn't provide a genuine transaction key.

The accepted records are written to `curated/`, partitioned by country. `monthly_sales/` contains sales, profit and units grouped by month, country, segment and product. For a reporting margin, I divide total profit by total sales rather than averaging individual group margins.

`run_summary.json` checks that the input count equals accepted + rejected + superseded. That tells me every row has been accounted for; it doesn't replace checking the financial calculations. The current job overwrites its outputs, so it isn't an atomic production publish.

## AWS equivalent

The local job reads and writes files on disk. In AWS, S3 provides the input/output paths and Glue runs the Spark job. The Glue entry point uses the same transformation module, supplied as an extra Python file. Terraform currently covers the S3 bucket and public access settings; it doesn't create the Glue role or job.

To investigate a failure, I'd first check the input schema and the error or job logs, then the rejected rows and reconciliation. For incorrect sales totals I'd check the validation and version counts before the aggregate calculation. Actual runs and issues belong in `Solutions/`.
