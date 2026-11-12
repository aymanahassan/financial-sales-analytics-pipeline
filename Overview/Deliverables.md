# Sales reporting exercise

## Requirement

The scenario is a consumer goods business receiving sales extracts from regional teams. Finance wants monthly figures without having to rebuild the same spreadsheet report each time. The input for this exercise is Microsoft's Financial Sample workbook, not a company system.

I used the sample to work through three reporting questions:

1. What are total sales by month, product and segment?
2. Which countries have the highest sales, and how much profit do they make?
3. How are profit and profit margin changing month by month?

The workbook has 700 rows but no transaction ID. I assign a source-row reference when converting it to CSV. The generated test records have their own IDs, which I use when checking record versions.

## What the pipeline needs to do

| Step | Check |
| --- | --- |
| Prepare the source | Read the workbook and export the sales fields to CSV |
| Generate test data | Produce repeatable batches with a fixed seed, including deliberate bad records and version updates |
| Validate | Check required fields, dates, numeric values, currency and financial calculations |
| Handle versions | Keep the latest valid version for each generated record ID |
| Write outputs | Save accepted rows and monthly reporting aggregates as Parquet |
| Reconcile | Account for input rows across accepted, rejected and superseded records |
| Run on AWS | Test the same transformation logic in Glue and inspect the S3 outputs and logs when configured |

I treat the figures as GBP because the source doesn't specify a currency. This is an assumption for the exercise, not a conversion. The generated data is useful for testing processing behaviour, but isn't suitable for real sales forecasts.
