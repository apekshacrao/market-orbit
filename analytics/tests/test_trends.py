import json
import datetime
import numpy as np
import pandas as pd
import pytest

from analytics.trends.customer_trends import analyze_trends


def test_daily_aggregation_spend_conversions_clicks_impressions():
    """1. Daily aggregation of spend, conversions, clicks, and impressions."""
    data = [
        {"date": "2026-09-01", "channel": "Google", "spend": 100.0, "conversions": 10, "clicks": 200, "impressions": 4000, "revenue": 300.0},
        {"date": "2026-09-02", "channel": "Meta", "spend": 150.0, "conversions": 15, "clicks": 300, "impressions": 6000, "revenue": 450.0},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    ts = result["time_series"]
    assert ts["has_time_series"] is True
    assert ts["status"] == "available"
    assert len(ts["timeline"]) == 2

    day1 = ts["timeline"][0]
    assert day1["date"] == "2026-09-01"
    assert day1["spend"] == 100.0
    assert day1["conversions"] == 10
    assert day1["clicks"] == 200
    assert day1["impressions"] == 4000
    assert day1["revenue"] == 300.0

    day2 = ts["timeline"][1]
    assert day2["date"] == "2026-09-02"
    assert day2["spend"] == 150.0
    assert day2["conversions"] == 15
    assert day2["clicks"] == 300
    assert day2["impressions"] == 6000
    assert day2["revenue"] == 450.0


def test_chronological_ordering_shuffled_inputs():
    """2. Correct chronological ordering when input rows are shuffled."""
    data = [
        {"date": "2026-09-20", "channel": "Google", "spend": 50.0, "conversions": 2},
        {"date": "2026-09-01", "channel": "Google", "spend": 100.0, "conversions": 5},
        {"date": "2026-09-10", "channel": "Google", "spend": 75.0, "conversions": 3},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    ts = result["time_series"]
    assert ts["has_time_series"] is True
    dates = [item["date"] for item in ts["timeline"]]
    assert dates == ["2026-09-01", "2026-09-10", "2026-09-20"]
    assert ts["start_date"] == "2026-09-01"
    assert ts["end_date"] == "2026-09-20"
    assert ts["date_range"]["total_days"] == 20
    assert ts["distinct_dates_count"] == 3


def test_multiple_records_on_same_date():
    """3. Multiple records on the same date are accurately aggregated."""
    data = [
        {"date": "2026-09-01", "channel": "Google", "spend": 100.0, "conversions": 5, "clicks": 50, "impressions": 1000, "revenue": 200.0},
        {"date": "2026-09-01", "channel": "Meta", "spend": 150.0, "conversions": 10, "clicks": 100, "impressions": 2000, "revenue": 300.0},
        {"date": "2026-09-02", "channel": "Google", "spend": 200.0, "conversions": 12, "clicks": 120, "impressions": 2400, "revenue": 400.0},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    ts = result["time_series"]
    assert len(ts["timeline"]) == 2
    day1 = ts["timeline"][0]
    assert day1["date"] == "2026-09-01"
    assert day1["spend"] == 250.0
    assert day1["conversions"] == 15
    assert day1["clicks"] == 150
    assert day1["impressions"] == 3000
    assert day1["revenue"] == 500.0


def test_non_contiguous_dates_no_synthetic_entries():
    """4. Non-contiguous dates without synthetic timeline entries."""
    data = [
        {"date": "2026-09-01", "channel": "Search", "spend": 100.0, "conversions": 5},
        {"date": "2026-09-08", "channel": "Search", "spend": 200.0, "conversions": 10},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    ts = result["time_series"]
    assert ts["distinct_dates_count"] == 2
    assert len(ts["timeline"]) == 2
    assert [item["date"] for item in ts["timeline"]] == ["2026-09-01", "2026-09-08"]
    assert ts["date_range"]["total_days"] == 8


def test_missing_date_column():
    """5. Missing date column handled gracefully with insufficient_data status."""
    data = [
        {"channel": "Google", "spend": 100.0, "conversions": 5},
        {"channel": "Meta", "spend": 150.0, "conversions": 10},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    ts = result["time_series"]
    assert ts["has_time_series"] is False
    assert ts["status"] == "insufficient_data"
    assert ts["timeline"] == []
    assert ts["distinct_dates_count"] == 0
    # Channel breakdown must still be computed
    assert "Google" in result["channel_breakdown"]
    assert "Meta" in result["channel_breakdown"]


def test_null_and_invalid_dates():
    """6. Null and invalid dates are ignored for time series while preserving valid channel breakdown."""
    data = [
        {"date": None, "channel": "Email", "spend": 20.0, "conversions": 1},
        {"date": "", "channel": "Email", "spend": 30.0, "conversions": 2},
        {"date": "not-a-date", "channel": "Social", "spend": 40.0, "conversions": 2},
        {"date": "2026-02-30", "channel": "Social", "spend": 50.0, "conversions": 3},  # Invalid calendar date
        {"date": "2026-09-01", "channel": "Search", "spend": 100.0, "conversions": 10},
        {"date": "2026-09-02", "channel": "Search", "spend": 120.0, "conversions": 12},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    ts = result["time_series"]
    assert ts["has_time_series"] is True
    assert ts["distinct_dates_count"] == 2
    assert [item["date"] for item in ts["timeline"]] == ["2026-09-01", "2026-09-02"]

    # All channels including rows with invalid dates must be in channel_breakdown
    assert "Email" in result["channel_breakdown"]
    assert "Social" in result["channel_breakdown"]
    assert "Search" in result["channel_breakdown"]
    assert result["channel_breakdown"]["Email"]["spend"] == 50.0


def test_single_date_datasets_and_insufficient_coverage():
    """7. Single-date datasets report insufficient_data and empty timeline."""
    data = [
        {"date": "2026-09-01", "channel": "Google", "spend": 100.0, "conversions": 5},
        {"date": "2026-09-01", "channel": "Meta", "spend": 200.0, "conversions": 10},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    ts = result["time_series"]
    assert ts["has_time_series"] is False
    assert ts["status"] == "insufficient_data"
    assert ts["distinct_dates_count"] == 1
    assert ts["timeline"] == []
    assert "Google" in result["channel_breakdown"]


def test_correct_derived_metrics():
    """8. Correct daily derived metrics: CPA, CPC, CTR, conversion rate, ROAS, and ROI."""
    data = [
        {
            "date": "2026-09-01",
            "channel": "Google",
            "spend": 500.0,
            "conversions": 25,
            "clicks": 250,
            "impressions": 5000,
            "revenue": 1500.0,
        },
        {
            "date": "2026-09-02",
            "channel": "Google",
            "spend": 200.0,
            "conversions": 10,
            "clicks": 100,
            "impressions": 2000,
            "revenue": 400.0,
        },
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    day1 = result["time_series"]["timeline"][0]
    assert day1["cpa"] == 20.0  # 500 / 25
    assert day1["cpc"] == 2.0   # 500 / 250
    assert day1["ctr"] == 5.0   # (250 / 5000) * 100
    assert day1["conversion_rate"] == 10.0  # (25 / 250) * 100
    assert day1["roas"] == 3.0  # 1500 / 500
    assert day1["roi"] == 200.0 # ((1500 - 500) / 500) * 100


def test_zero_denominators_json_safe_null():
    """9. Zero denominators return None and serialize to valid JSON nulls."""
    data = [
        {
            "date": "2026-09-01",
            "channel": "Search",
            "spend": 0.0,
            "conversions": 0,
            "clicks": 0,
            "impressions": 0,
            "revenue": None,
        },
        {
            "date": "2026-09-02",
            "channel": "Display",
            "spend": 100.0,
            "conversions": 0,
            "clicks": 0,
            "impressions": 500,
            "revenue": None,
        },
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    day1 = result["time_series"]["timeline"][0]
    assert day1["cpa"] is None
    assert day1["cpc"] is None
    assert day1["ctr"] is None
    assert day1["conversion_rate"] is None
    assert day1["roas"] is None
    assert day1["roi"] is None

    day2 = result["time_series"]["timeline"][1]
    assert day2["cpa"] is None
    assert day2["cpc"] is None
    assert day2["ctr"] == 0.0  # 0 clicks / 500 impressions * 100 = 0.0
    assert day2["conversion_rate"] is None

    # Strict JSON serialization without NaN or Infinity
    serialized = json.dumps(result, allow_nan=False)
    assert "NaN" not in serialized
    assert "Infinity" not in serialized


def test_missing_revenue_versus_explicit_zero_revenue():
    """10. Missing revenue vs explicitly zero revenue remains distinguishable."""
    data = [
        {"date": "2026-09-01", "channel": "Search", "spend": 100.0, "conversions": 5, "revenue": None},
        {"date": "2026-09-02", "channel": "Search", "spend": 100.0, "conversions": 5, "revenue": 0.0},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    timeline = result["time_series"]["timeline"]
    # Day 1: untracked revenue
    assert timeline[0]["revenue"] is None
    assert timeline[0]["roas"] is None
    assert timeline[0]["roi"] is None

    # Day 2: explicitly zero revenue
    assert timeline[1]["revenue"] == 0.0
    assert timeline[1]["roas"] == 0.0
    assert timeline[1]["roi"] == -100.0


def test_partially_missing_revenue_daily_aggregation():
    """11. Partially missing revenue within a day is treated as incomplete (None)."""
    data = [
        {"date": "2026-09-01", "channel": "Google", "spend": 100.0, "conversions": 5, "revenue": 300.0},
        {"date": "2026-09-01", "channel": "Meta", "spend": 100.0, "conversions": 5, "revenue": None},
        {"date": "2026-09-02", "channel": "Google", "spend": 100.0, "conversions": 5, "revenue": 250.0},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    day1 = result["time_series"]["timeline"][0]
    assert day1["revenue"] is None
    assert day1["roas"] is None
    assert day1["roi"] is None

    day2 = result["time_series"]["timeline"][1]
    assert day2["revenue"] == 250.0
    assert day2["roas"] == 2.5


def test_empty_dataset_and_missing_optional_metrics():
    """12. Handles empty datasets and missing optional metric columns."""
    empty_result = analyze_trends(pd.DataFrame())
    assert empty_result["channel_breakdown"] == {}
    assert empty_result["time_series"]["has_time_series"] is False
    assert empty_result["time_series"]["status"] == "insufficient_data"
    assert empty_result["time_series"]["timeline"] == []

    # Minimal columns: only date and conversions
    minimal_df = pd.DataFrame([
        {"date": "2026-09-01", "conversions": 5},
        {"date": "2026-09-02", "conversions": 10},
    ])
    min_res = analyze_trends(minimal_df)
    assert min_res["time_series"]["has_time_series"] is True
    day1 = min_res["time_series"]["timeline"][0]
    assert day1["spend"] == 0.0
    assert day1["conversions"] == 5
    assert day1["clicks"] == 0
    assert day1["impressions"] == 0
    assert day1["revenue"] is None
    assert day1["cpa"] == 0.0  # 0.0 spend / 5 conversions = 0.0
    assert day1["cpc"] is None


def test_preservation_of_channel_breakdown_behavior():
    """13. Existing channel breakdown behavior and shape are preserved."""
    data = [
        {"date": "2026-09-01", "channel": "Google", "spend": 200.0, "conversions": 15, "revenue": 800.0},
        {"date": "2026-09-02", "channel": "Meta", "spend": 300.0, "conversions": 20, "revenue": 900.0},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    cb = result["channel_breakdown"]
    assert "Google" in cb
    assert "Meta" in cb
    assert cb["Google"]["spend"] == 200.0
    assert cb["Google"]["revenue"] == 800.0
    assert cb["Google"]["conversions"] == 15
    assert cb["Meta"]["spend"] == 300.0
    assert cb["Meta"]["revenue"] == 900.0
    assert cb["Meta"]["conversions"] == 20


def test_backward_compatibility_with_all_callers():
    """14. Preserves backward compatibility with AnalysisService result storage."""
    data = [
        {"date": "2026-09-01", "channel": "Google", "spend": 100.0, "conversions": 10},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    assert "channel_breakdown" in result
    assert "time_series" in result
    assert isinstance(result["channel_breakdown"], dict)
    assert isinstance(result["time_series"], dict)
    # Stored into PostgreSQL JSONB without failure
    json_str = json.dumps(result, allow_nan=False)
    assert isinstance(json_str, str)

