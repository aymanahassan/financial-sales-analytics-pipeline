# Issues and limitations

## Decisions made during the build

- **No transaction ID in the workbook.** I use a source-row reference for extraction and generated IDs for the test records. I don't assume two identical-looking sales rows are duplicates.
- **No currency field.** I've treated the figures as GBP for this exercise and check that generated records use that code.
- **Negative profit.** I don't reject a loss-making sale just because profit is below zero; the arithmetic still has to reconcile.
- **Generated bad records.** These are intentional so I can test rejection reasons and record counts.

## Still to verify

- Local Spark batch results and tests on the final version of the code.
- The larger synthetic batch and its reconciliation totals.
- The Glue run, permissions, S3 paths and CloudWatch logs.

The local job writes outputs in overwrite mode. That's sufficient for this exercise, but not how I'd publish production data without additional controls.

## Actual errors encountered

Added the command, error, fix and rerun result here after an observed failure. No FSAP failure is recorded in this packaged version.
