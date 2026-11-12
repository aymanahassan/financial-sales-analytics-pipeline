"""Tests for financial sales validation, versioning and aggregation."""

import sys
from pathlib import Path

import pytest
from pyspark.sql import SparkSession

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from financial_pipeline import SCHEMA, aggregate, classify, reconcile


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("financial-pipeline-tests")
        .getOrCreate()
    )
    yield session
    session.stop()


def row(
    id="a",
    version=1,
    country="Canada",
    date="2014-01-01",
    sales=20.0,
    profit=14.0,
    units=2.0,
    source="row1",
):
    return (
        id,
        source,
        version,
        "2026-11-12T09:00:00",
        "Government",
        country,
        "Carretera",
        "None",
        units,
        3.0,
        10.0,
        20.0,
        0.0,
        sales,
        6.0,
        profit,
        date,
        "GBP",
    )


def test_classification_and_reconciliation(spark):
    raw = spark.createDataFrame(
        [
            row(),
            row(version=2, source="row1-v2"),
            row(id="b", country=""),
            row(id="c", sales=22.0),
            row(id="d", date="bad"),
            row(id="e", profit=-5.0, sales=20.0),
        ],
        SCHEMA,
    )

    curated, quarantine, superseded = classify(raw)
    counts = reconcile(raw, curated, quarantine, superseded)

    assert counts == {
        "raw": 6,
        "curated": 1,
        "quarantined": 4,
        "superseded": 1,
        "balanced": True,
    }
    assert curated.first().version == 2
    assert {r.rejection_reason for r in quarantine.collect()} == {
        "missing_identifier_or_dimension",
        "financial_reconciliation_failed",
        "invalid_date",
    }


def test_negative_profit_allowed_if_consistent(spark):
    loss_row = list(row(id="loss", sales=4.0, profit=-2.0))
    loss_row[12] = 16.0  # Discount: gross sales 20.0 less 16.0 = net sales 4.0
    raw = spark.createDataFrame([tuple(loss_row)], SCHEMA)

    curated, quarantine, _ = classify(raw)
    assert curated.count() == 1
    assert quarantine.count() == 0


def test_aggregate(spark):
    raw = spark.createDataFrame(
        [row(id="a"), row(id="b", source="row2")], SCHEMA
    )
    curated, _, _ = classify(raw)
    grouped = aggregate(curated).collect()

    assert len(grouped) == 1
    assert grouped[0].record_count == 2
    assert grouped[0].total_sales == 40.0


def test_unsupported_currency_quarantined(spark):
    bad_row = list(row())
    bad_row[-1] = "EUR"
    raw = spark.createDataFrame([tuple(bad_row)], SCHEMA)

    curated, quarantine, _ = classify(raw)
    assert curated.count() == 0
    assert quarantine.first().rejection_reason == "unsupported_currency"


def test_financial_mismatch(spark):
    raw = spark.createDataFrame([row(sales=19.0)], SCHEMA)
    _, quarantine, _ = classify(raw)
    assert quarantine.first().rejection_reason == "financial_reconciliation_failed"
