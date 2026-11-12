# Architecture

```text
Financial Sample workbook (700 rows)
                |
      prepare_source.py
                |
         source_sales.csv
                |
      generate_events.py
                |
     sales_events.csv (synthetic)
                |
          Spark batch
         /     |      \
  curated  rejected  superseded
   Parquet    JSON       JSON
       |
 monthly_sales Parquet
       |
 sales, country and profit analysis
```

The local job reads a CSV and writes to local paths. For AWS, the equivalent input and output paths are in S3 and the Spark application is executed as an AWS Glue job. The shared transformation module is supplied to Glue as a Python dependency.

```text
S3 raw CSV -> Glue Spark job -> S3 curated / monthly_sales / quarantine / superseded
                          \-> CloudWatch job logs (reconciliation)
```

Terraform provisions S3 storage. IAM role creation, job configuration and deployment are separate tasks. No streaming path is connected to the financial batch pipeline.
