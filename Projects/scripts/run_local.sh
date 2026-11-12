#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
COUNT="${1:-1000}"
WORKBOOK="${2:-data/Financial_Sample.xlsx}"
python src/prepare_source.py --workbook "$WORKBOOK"
python src/generate_events.py --source data/source_sales.csv --count "$COUNT" --seed 42
spark-submit --master 'local[2]' src/spark_job.py --input data/sales_events.csv --output data/processed
python -m pytest -v
cat data/processed/run_summary.json
