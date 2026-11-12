# Results

## Reporting outputs

The Spark job writes `monthly_sales/` with month, country, segment, product, record count, sales, profit and units sold. I can use that output to check:

- Monthly sales totals and trends.
- Country rankings by sales and profit.
- Monthly profit margin (`total profit / total sales`, where sales are nonzero).

These results come from the generated test batch, not directly from the original 700-row workbook. Any figures included here need to be taken from an actual run.

## Checks so far

| Check | Status |
| --- | --- |
| Workbook extraction | Earlier local conversion reported 700 source rows; rerun on final version pending |
| GBP field and validation | Included in code; final test run pending |
| Generator and Spark tests | Included; final test run pending |
| Local batch reconciliation | Pending recorded output |
| AWS Glue run | Not yet verified |

## Reconciliation

The expected balance is `input = curated + quarantined + superseded`. I'll record the actual counts from `data/processed/run_summary.json` after the final run, along with the test result and any errors.
