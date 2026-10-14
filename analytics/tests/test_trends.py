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


def test_dimension_breakdowns_all_supported_dimensions():
    """15. Correct aggregation for each supported dimension (location, age_group, customer_segment, device)."""
    data = [
        {
            "channel": "Google",
            "spend": 100.0,
            "conversions": 5,
            "clicks": 50,
            "impressions": 1000,
            "revenue": 300.0,
            "location": "US",
            "age_group": "25-34",
            "customer_segment": "Enterprise",
            "device": "Desktop",
        },
        {
            "channel": "Meta",
            "spend": 200.0,
            "conversions": 10,
            "clicks": 100,
            "impressions": 2000,
            "revenue": 500.0,
            "location": "US",
            "age_group": "35-44",
            "customer_segment": "SMB",
            "device": "Mobile",
        },
        {
            "channel": "LinkedIn",
            "spend": 150.0,
            "conversions": 3,
            "clicks": 30,
            "impressions": 500,
            "revenue": 450.0,
            "location": "UK",
            "age_group": "25-34",
            "customer_segment": "Enterprise",
            "device": "Desktop",
        },
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    assert "dimension_breakdowns" in result
    dims = result["dimension_breakdowns"]
    assert set(dims.keys()) == {"location", "age_group", "customer_segment", "device"}

    # Check location breakdown
    us_loc = dims["location"]["US"]
    assert us_loc["spend"] == 300.0
    assert us_loc["conversions"] == 15
    assert us_loc["clicks"] == 150
    assert us_loc["impressions"] == 3000
    assert us_loc["revenue"] == 800.0

    uk_loc = dims["location"]["UK"]
    assert uk_loc["spend"] == 150.0
    assert uk_loc["conversions"] == 3
    assert uk_loc["revenue"] == 450.0

    # Check age_group
    age_25_34 = dims["age_group"]["25-34"]
    assert age_25_34["spend"] == 250.0
    assert age_25_34["conversions"] == 8
    assert age_25_34["revenue"] == 750.0

    # Check customer_segment
    ent = dims["customer_segment"]["Enterprise"]
    assert ent["spend"] == 250.0
    assert ent["conversions"] == 8

    # Check device
    desktop = dims["device"]["Desktop"]
    assert desktop["spend"] == 250.0
    assert desktop["clicks"] == 80


def test_dimension_breakdowns_multiple_categories_and_deterministic_ordering():
    """16. Multiple categories within dimensions return in deterministic alphabetical order."""
    data = [
        {"location": "Tokyo", "spend": 50.0, "conversions": 2},
        {"location": "Berlin", "spend": 80.0, "conversions": 4},
        {"location": "New York", "spend": 120.0, "conversions": 6},
        {"location": "London", "spend": 90.0, "conversions": 5},
    ]
    df = pd.DataFrame(data)

    # Shuffled order of rows
    df_shuffled = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    res1 = analyze_trends(df)
    res2 = analyze_trends(df_shuffled)

    categories1 = list(res1["dimension_breakdowns"]["location"].keys())
    categories2 = list(res2["dimension_breakdowns"]["location"].keys())

    expected_order = ["Berlin", "London", "New York", "Tokyo"]
    assert categories1 == expected_order
    assert categories2 == expected_order
    assert res1["dimension_breakdowns"] == res2["dimension_breakdowns"]


def test_dimension_breakdowns_missing_columns_and_null_empty_values():
    """17. Handles missing dimension columns, nulls, whitespace, and NaN values without fabricating categories."""
    data = [
        {"spend": 100.0, "conversions": 5, "location": "US-East", "device": "Mobile"},
        {"spend": 50.0, "conversions": 2, "location": None, "device": "  "},
        {"spend": 40.0, "conversions": 1, "location": "", "device": "Mobile"},
        {"spend": 30.0, "conversions": 1, "location": "   ", "device": None},
        {"spend": 20.0, "conversions": 1, "location": "nan", "device": "null"},
        {"spend": 60.0, "conversions": 3, "location": "US-West", "device": "Desktop"},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    dims = result["dimension_breakdowns"]
    # Only location and device were present; age_group and customer_segment were missing from columns
    assert "age_group" not in dims
    assert "customer_segment" not in dims
    assert "location" in dims
    assert "device" in dims

    # Location must only have valid categories
    assert set(dims["location"].keys()) == {"US-East", "US-West"}
    assert dims["location"]["US-East"]["spend"] == 100.0
    assert dims["location"]["US-West"]["spend"] == 60.0

    # Device must only have valid categories
    assert set(dims["device"].keys()) == {"Desktop", "Mobile"}
    assert dims["device"]["Mobile"]["spend"] == 140.0
    assert dims["device"]["Mobile"]["conversions"] == 6
    assert dims["device"]["Desktop"]["spend"] == 60.0


def test_dimension_independence():
    """18. Missing values in one dimension do not prevent analysis of another dimension."""
    data = [
        {"spend": 100.0, "conversions": 5, "location": None, "device": "Mobile"},
        {"spend": 150.0, "conversions": 8, "location": "", "device": "Desktop"},
        {"spend": 200.0, "conversions": 10, "location": np.nan, "device": "Tablet"},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    dims = result["dimension_breakdowns"]
    # location has no usable values, so it must not be present
    assert "location" not in dims
    # device has usable values and must be present
    assert "device" in dims
    assert set(dims["device"].keys()) == {"Desktop", "Mobile", "Tablet"}
    assert dims["device"]["Mobile"]["spend"] == 100.0
    assert dims["device"]["Desktop"]["spend"] == 150.0
    assert dims["device"]["Tablet"]["spend"] == 200.0


def test_dimension_breakdowns_derived_metrics_and_percentage_scaling():
    """19. Calculates CPA, CPC, CTR, conversion rate, ROAS, and ROI with proper percentage scaling."""
    data = [
        {
            "location": "APAC",
            "spend": 500.0,
            "conversions": 25,
            "clicks": 250,
            "impressions": 5000,
            "revenue": 1500.0,
        }
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    apac = result["dimension_breakdowns"]["location"]["APAC"]
    assert apac["cpa"] == 20.0              # 500 / 25
    assert apac["cpc"] == 2.0               # 500 / 250
    assert apac["ctr"] == 5.0               # (250 / 5000) * 100 -> 5.0%
    assert apac["conversion_rate"] == 10.0   # (25 / 250) * 100 -> 10.0%
    assert apac["roas"] == 3.0              # 1500 / 500 -> 3.0 ratio
    assert apac["roi"] == 200.0             # ((1500 - 500) / 500) * 100 -> 200.0%


def test_dimension_breakdowns_zero_denominators_and_null_metrics():
    """20. Handles zero spend, conversions, clicks, impressions with None for undefined metrics."""
    data = [
        {
            "device": "SmartTV",
            "spend": 0.0,
            "conversions": 0,
            "clicks": 0,
            "impressions": 0,
            "revenue": None,
        },
        {
            "device": "Console",
            "spend": 100.0,
            "conversions": 0,
            "clicks": 0,
            "impressions": 200,
            "revenue": None,
        },
        {
            "device": "Wearable",
            "spend": 50.0,
            "conversions": 0,
            "clicks": 10,
            "impressions": 200,
            "revenue": None,
        },
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    devs = result["dimension_breakdowns"]["device"]

    smart_tv = devs["SmartTV"]
    assert smart_tv["cpa"] is None
    assert smart_tv["cpc"] is None
    assert smart_tv["ctr"] is None
    assert smart_tv["conversion_rate"] is None
    assert smart_tv["roas"] is None
    assert smart_tv["roi"] is None

    console = devs["Console"]
    assert console["cpa"] is None
    assert console["cpc"] is None
    assert console["ctr"] == 0.0          # 0 clicks / 200 impressions * 100 = 0.0
    assert console["conversion_rate"] is None

    wearable = devs["Wearable"]
    assert wearable["cpc"] == 5.0         # 50 / 10
    assert wearable["ctr"] == 5.0         # (10 / 200) * 100 = 5.0
    assert wearable["conversion_rate"] == 0.0 # 0 conversions / 10 clicks * 100 = 0.0
    assert wearable["cpa"] is None        # 0 conversions


def test_dimension_breakdowns_revenue_semantics_missing_zero_partial():
    """21. Distinguishes missing revenue (None), explicit zero (0.0/-100%), and partially missing revenue (None)."""
    data = [
        # Missing revenue
        {"customer_segment": "Untracked", "spend": 100.0, "conversions": 5, "revenue": None},
        # Explicitly zero revenue
        {"customer_segment": "ZeroRev", "spend": 100.0, "conversions": 5, "revenue": 0.0},
        # Partially missing revenue
        {"customer_segment": "PartialRev", "spend": 100.0, "conversions": 5, "revenue": 300.0},
        {"customer_segment": "PartialRev", "spend": 100.0, "conversions": 5, "revenue": None},
        # Completely tracked revenue
        {"customer_segment": "TrackedRev", "spend": 100.0, "conversions": 5, "revenue": 200.0},
        {"customer_segment": "TrackedRev", "spend": 100.0, "conversions": 5, "revenue": 100.0},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    segs = result["dimension_breakdowns"]["customer_segment"]

    # 1. Untracked
    assert segs["Untracked"]["revenue"] is None
    assert segs["Untracked"]["roas"] is None
    assert segs["Untracked"]["roi"] is None

    # 2. Explicit zero revenue
    assert segs["ZeroRev"]["revenue"] == 0.0
    assert segs["ZeroRev"]["roas"] == 0.0
    assert segs["ZeroRev"]["roi"] == -100.0

    # 3. Partially missing revenue
    assert segs["PartialRev"]["revenue"] is None
    assert segs["PartialRev"]["roas"] is None
    assert segs["PartialRev"]["roi"] is None

    # 4. Completely tracked revenue
    assert segs["TrackedRev"]["revenue"] == 300.0
    assert segs["TrackedRev"]["roas"] == 1.5   # 300 / 200
    assert segs["TrackedRev"]["roi"] == 50.0  # ((300 - 200) / 200) * 100


def test_dimension_breakdowns_empty_datasets_and_no_usable_dimensions():
    """22. Handles empty dataframes and datasets with no usable dimension values."""
    res_empty = analyze_trends(pd.DataFrame())
    assert res_empty["dimension_breakdowns"] == {}

    res_none = analyze_trends(None)
    assert res_none["dimension_breakdowns"] == {}

    df_no_usable = pd.DataFrame([
        {"location": None, "age_group": "", "device": "nan", "spend": 100.0},
        {"location": "   ", "age_group": "None", "device": "null", "spend": 200.0},
    ])
    res_no_usable = analyze_trends(df_no_usable)
    assert res_no_usable["dimension_breakdowns"] == {}


def test_backward_compatibility_channel_breakdown_and_time_series():
    """23. Preserves channel_breakdown and time_series structures alongside dimension_breakdowns."""
    data = [
        {
            "date": "2026-09-01",
            "channel": "Google",
            "spend": 150.0,
            "conversions": 10,
            "clicks": 100,
            "impressions": 2000,
            "revenue": 450.0,
            "location": "US",
        },
        {
            "date": "2026-09-02",
            "channel": "Meta",
            "spend": 200.0,
            "conversions": 12,
            "clicks": 120,
            "impressions": 2400,
            "revenue": 600.0,
            "location": "EU",
        },
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    # 1. channel_breakdown
    assert "channel_breakdown" in result
    assert "Google" in result["channel_breakdown"]
    assert "Meta" in result["channel_breakdown"]
    assert result["channel_breakdown"]["Google"]["spend"] == 150.0
    assert result["channel_breakdown"]["Google"]["revenue"] == 450.0
    assert result["channel_breakdown"]["Google"]["conversions"] == 10

    # 2. time_series
    assert "time_series" in result
    assert result["time_series"]["has_time_series"] is True
    assert result["time_series"]["status"] == "available"
    assert len(result["time_series"]["timeline"]) == 2

    # 3. dimension_breakdowns
    assert "dimension_breakdowns" in result
    assert "location" in result["dimension_breakdowns"]
    assert set(result["dimension_breakdowns"]["location"].keys()) == {"EU", "US"}


def test_strict_json_serialization_allow_nan_false():
    """24. Dimension breakdowns serialize cleanly under strict JSON serialization without NaN or Infinity."""
    data = [
        {"location": "US", "device": "Mobile", "spend": 0.0, "conversions": 0, "clicks": 0, "impressions": 0, "revenue": None},
        {"location": "EU", "device": "Desktop", "spend": 100.0, "conversions": 0, "clicks": 0, "impressions": 500, "revenue": 0.0},
        {"location": "APAC", "device": "Tablet", "spend": 200.0, "conversions": 5, "clicks": 50, "impressions": 1000, "revenue": 600.0},
    ]
    df = pd.DataFrame(data)
    result = analyze_trends(df)

    # Must serialize with allow_nan=False
    json_str = json.dumps(result, allow_nan=False)
    assert isinstance(json_str, str)
    assert "NaN" not in json_str
    assert "Infinity" not in json_str

    parsed = json.loads(json_str)
    assert parsed["dimension_breakdowns"]["location"]["US"]["cpa"] is None
    assert parsed["dimension_breakdowns"]["location"]["EU"]["revenue"] == 0.0
    assert parsed["dimension_breakdowns"]["location"]["APAC"]["roas"] == 3.0


def test_backend_caller_compatibility_with_cleaned_dataset():
    """25. Compatibility with AnalysisService workflow using clean_dataset."""
    from analytics.preprocessing.cleaner import clean_dataset

    raw_campaigns = [
        {
            "campaign_name": "Summer Launch",
            "channel": "Google",
            "spend": 300.0,
            "conversions": 15,
            "clicks": 150,
            "impressions": 3000,
            "revenue": 900.0,
            "date": "2026-09-01",
            "location": "North America",
            "device": "Mobile",
        },
        {
            "campaign_name": "Summer Launch 2",
            "channel": "Google",
            "spend": 200.0,
            "conversions": 10,
            "clicks": 100,
            "impressions": 2000,
            "revenue": 500.0,
            "date": "2026-09-02",
            "location": "North America",
            "device": "Desktop",
        },
    ]
    cleaned_df = clean_dataset(raw_campaigns)
    result = analyze_trends(cleaned_df)

    assert "channel_breakdown" in result
    assert "time_series" in result
    assert "dimension_breakdowns" in result
    assert "location" in result["dimension_breakdowns"]
    assert "device" in result["dimension_breakdowns"]
    assert result["dimension_breakdowns"]["location"]["North America"]["spend"] == 500.0
    assert result["dimension_breakdowns"]["location"]["North America"]["conversions"] == 25
    assert result["dimension_breakdowns"]["location"]["North America"]["revenue"] == 1400.0


