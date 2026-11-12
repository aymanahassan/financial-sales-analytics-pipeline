# Financial Sales Analytics Pipeline

I built this while getting up to speed with AWS Glue and PySpark. Most of my previous data engineering work has been around SQL Server, Azure Data Factory, Azure Data Lakes Gen2 and Power BI, so I wanted to take a familiar reporting problem and work through it using Spark and AWS.

I started with a separate six-record Spark/Glue exercise to understand the basic flow. For this project I used Microsoft's Financial Sample workbook (700 rows) and built a batch pipeline around three questions:

- How are sales changing month by month?
- Which countries bring in the most sales and profit?
- How does profit margin change over time?

The scripts convert the workbook to CSV, generate repeatable test records, check the data in PySpark and write Parquet outputs for reporting. Rejected records and older record versions are saved separately so I can account for what happened to each input row.

## Folders

- `Overview/` — the reporting requirement, design and processing notes
- `Projects/` — Python and Spark code, tests, Glue entry point and Terraform
- `Solutions/` — results, checks and issues

## Run it locally

You need Python 3.11, Java 17, `uv` and `spark-submit` available on your machine. From `Projects/`:

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
bash scripts/run_local.sh 1000
```

The script uses `data/Financial_Sample.xlsx`, generates 1,000 test records, runs Spark and then runs the tests. Once the smaller run works, you can use `bash scripts/run_local.sh 100000` to try a larger batch.

Check `data/processed/run_summary.json` for the record counts. The Parquet outputs are in `data/processed/curated/` and `data/processed/monthly_sales/`. Invalid rows go to `quarantine/` and older valid versions to `superseded/`.

## AWS setup

The Terraform configuration is for an S3 bucket in Stockholm (`eu-north-1`) using the `fsap` CLI profile. The Glue script is included, but setting up its execution role and job is separate from the Terraform S3 setup. I record local and AWS runs separately in `Solutions/Results.md`.

## A couple of assumptions

The Microsoft workbook doesn't specify a currency, so I've treated the amounts as GBP for this exercise; no conversion takes place. The additional records are generated test data based on the sample, not new real-world sales. This is a batch-processing exercise, not a live reporting system.
