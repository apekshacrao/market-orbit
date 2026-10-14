import json
import numpy as np
import pandas as pd
import pytest

from analytics.forecasting.data_prep import prepare_daily_series
from analytics.forecasting import prepare_daily_series as package_entrypoint
from analytics.kpi.metrics import calculate_kpis
from analytics.performance.ranking import rank_campaigns
from analytics.trends.customer_trends import analyze_trends
from analytics.segmentation.cohorts import classify_campaign_cohorts
from analytics.segmentation.portfolio import profile_segment_portfolio


def test_valid_dates_and_chronological_ordering():
    """1. Valid dates and chronological ordering."""
    # Data provided out of order
    data = [
        {"date": "2026-08-03", "spend": 300.0, "conversions": 30},
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10},
        {"date": "2026-08-02", "spend": 200.0, "conversions": 20},
    ]
    df = pd.DataFrame(data)
    result = prepare_daily_series(df)

    assert result["is_available"] is True
    assert result["metadata"]["historical_dates_count"] == 3
    assert result["metadata"]["start_date"] == "2026-08-01"
    assert result["metadata"]["end_date"] == "2026-08-03"

    dates = [row["date"] for row in result["series"]]
    assert dates == ["2026-08-01", "2026-08-02", "2026-08-03"]
    assert result["series"][0]["spend"] == 100.0
    assert result["series"][1]["spend"] == 200.0
    assert result["series"][2]["spend"] == 300.0


def test_strict_date_parsing_and_invalid_date_exclusion_diagnostics():
    """2. Strict date parsing and invalid-date exclusion diagnostics."""
    data = [
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10},
        {"date": "08/02/2026", "spend": 200.0, "conversions": 20},  # invalid format
        {"date": "invalid-date", "spend": 150.0, "conversions": 15}, # invalid string
        {"date": None, "spend": 50.0, "conversions": 5},            # null
        {"date": "   ", "spend": 50.0, "conversions": 5},            # whitespace
        {"date": "2026-08-02", "spend": 250.0, "conversions": 25},  # valid
    ]
    df = pd.DataFrame(data)
    result = prepare_daily_series(df)

    assert result["is_available"] is True
    meta = result["metadata"]
    assert meta["total_records_count"] == 6
    assert meta["excluded_records_count"] == 4
    assert meta["historical_dates_count"] == 2
    assert meta["start_date"] == "2026-08-01"
    assert meta["end_date"] == "2026-08-02"

    assert any("Excluded 4 record(s)" in w for w in result["warnings"])


def test_duplicate_date_aggregation():
    """3. Duplicate-date aggregation across multiple campaign records."""
    data = [
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10, "clicks": 50, "impressions": 1000},
        {"date": "2026-08-01", "spend": 150.0, "conversions": 15, "clicks": 75, "impressions": 1500},
        {"date": "2026-08-02", "spend": 200.0, "conversions": 20, "clicks": 100, "impressions": 2000},
    ]
    df = pd.DataFrame(data)
    result = prepare_daily_series(df)

    assert result["is_available"] is True
    assert len(result["series"]) == 2

    day1 = result["series"][0]
    assert day1["date"] == "2026-08-01"
    assert day1["spend"] == 250.0
    assert day1["conversions"] == 25
    assert day1["clicks"] == 125
    assert day1["impressions"] == 2500

    day2 = result["series"][1]
    assert day2["date"] == "2026-08-02"
    assert day2["spend"] == 200.0
    assert day2["conversions"] == 20


def test_empty_input_and_missing_date_column():
    """4. Empty input and missing date column handling."""
    # None input
    res_none = prepare_daily_series(None)
    assert res_none["is_available"] is False
    assert res_none["status"] == "unavailable"
    assert res_none["series"] == []
    assert res_none["metadata"]["historical_dates_count"] == 0

    # Empty DataFrame
    res_empty = prepare_daily_series(pd.DataFrame())
    assert res_empty["is_available"] is False
    assert res_empty["status"] == "unavailable"

    # Missing date column
    df_no_date = pd.DataFrame([{"spend": 100.0, "conversions": 10}])
    res_no_date = prepare_daily_series(df_no_date)
    assert res_no_date["is_available"] is False
    assert res_no_date["status"] == "unavailable"


def test_no_valid_dates():
    """5. DataFrame has date column but zero valid dates."""
    df_invalid = pd.DataFrame([
        {"date": "invalid", "spend": 100.0},
        {"date": None, "spend": 200.0},
        {"date": "   ", "spend": 300.0},
        {"date": "2026/01/01", "spend": 400.0},
    ])
    result = prepare_daily_series(df_invalid)

    assert result["is_available"] is False
    assert result["status"] == "no_valid_dates"
    assert result["metadata"]["historical_dates_count"] == 0
    assert result["metadata"]["excluded_records_count"] == 4
    assert result["series"] == []
    assert any("No valid calendar dates" in w for w in result["warnings"])


def test_contiguous_vs_non_contiguous_dates():
    """6. Contiguous versus non-contiguous timeline diagnostics."""
    # Contiguous 7-day series
    contiguous_data = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10}
        for i in range(1, 8)
    ]
    res_contig = prepare_daily_series(pd.DataFrame(contiguous_data))
    assert res_contig["is_available"] is True
    assert res_contig["status"] == "ready"
    assert res_contig["metadata"]["historical_dates_count"] == 7
    assert res_contig["metadata"]["calendar_span_days"] == 7
    assert res_contig["metadata"]["missing_dates_count"] == 0
    assert res_contig["metadata"]["is_contiguous"] is True
    assert res_contig["metadata"]["has_minimum_dates"] is True
    assert res_contig["metadata"]["has_seasonal_dates"] is False  # 7 < 14
    assert res_contig["metadata"]["contiguous_dates_count"] == 7

    # Non-contiguous series: Aug 1, Aug 2, Aug 4, Aug 5 (Aug 3 missing)
    non_contig_data = [
        {"date": "2026-08-01", "spend": 100.0},
        {"date": "2026-08-02", "spend": 100.0},
        {"date": "2026-08-04", "spend": 100.0},
        {"date": "2026-08-05", "spend": 100.0},
    ]
    res_non_contig = prepare_daily_series(pd.DataFrame(non_contig_data))
    assert res_non_contig["is_available"] is True
    assert res_non_contig["status"] == "insufficient_history"  # 4 < 7
    assert res_non_contig["metadata"]["historical_dates_count"] == 4
    assert res_non_contig["metadata"]["calendar_span_days"] == 5
    assert res_non_contig["metadata"]["missing_dates_count"] == 1
    assert res_non_contig["metadata"]["is_contiguous"] is False
    assert res_non_contig["metadata"]["contiguous_dates_count"] == 2  # max streak is 2
    assert any("contains 1 unobserved calendar date(s)" in w for w in res_non_contig["warnings"])


def test_observed_zeros_vs_unresolved_date_gaps():
    """7. Distinguishes observed zeros from unobserved date gaps."""
    data = [
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10},
        {"date": "2026-08-02", "spend": 0.0, "conversions": 0},    # observed zero
        # 2026-08-03 is not in data (unobserved gap)
        {"date": "2026-08-04", "spend": 200.0, "conversions": 20},
    ]
    df = pd.DataFrame(data)
    result = prepare_daily_series(df)

    assert result["is_available"] is True
    assert len(result["series"]) == 3  # Only 3 observed dates in series

    # Observed zero is recorded explicitly
    day2 = result["series"][1]
    assert day2["date"] == "2026-08-02"
    assert day2["spend"] == 0.0
    assert day2["conversions"] == 0
    assert day2["is_observed"] is True

    # 2026-08-03 is not present in series, but documented in metadata
    series_dates = [s["date"] for s in result["series"]]
    assert "2026-08-03" not in series_dates
    assert result["metadata"]["missing_dates_count"] == 1
    assert result["metadata"]["is_contiguous"] is False


def test_no_unjustified_zero_filling_or_interpolation():
    """8. Verifies no fabricated synthetic rows are inserted into series."""
    # Dates with gap of 5 days: Aug 1 and Aug 7
    data = [
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10},
        {"date": "2026-08-07", "spend": 700.0, "conversions": 70},
    ]
    df = pd.DataFrame(data)
    result = prepare_daily_series(df)

    assert len(result["series"]) == 2
    assert [s["date"] for s in result["series"]] == ["2026-08-01", "2026-08-07"]
    assert result["metadata"]["calendar_span_days"] == 7
    assert result["metadata"]["missing_dates_count"] == 5
    assert result["metadata"]["is_contiguous"] is False
    assert any("contains 5 unobserved calendar date(s)" in w for w in result["warnings"])


def test_optional_clicks_and_impressions():
    """9. Optional clicks and impressions aggregation under repository semantics."""
    # Clicks and impressions omitted
    data_no_ci = [
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10},
    ]
    res_no_ci = prepare_daily_series(pd.DataFrame(data_no_ci))
    assert res_no_ci["series"][0]["clicks"] == 0
    assert res_no_ci["series"][0]["impressions"] == 0

    # Clicks and impressions populated
    data_with_ci = [
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10, "clicks": 45, "impressions": 850},
    ]
    res_ci = prepare_daily_series(pd.DataFrame(data_with_ci))
    assert res_ci["series"][0]["clicks"] == 45
    assert res_ci["series"][0]["impressions"] == 850


def test_complete_untracked_partially_missing_and_invalid_revenue():
    """10. Complete, untracked, partially missing, and invalid revenue handling."""
    # Case A: Complete revenue
    data_complete = [
        {"date": "2026-08-01", "spend": 100.0, "revenue": 300.0},
        {"date": "2026-08-02", "spend": 100.0, "revenue": 0.0},  # explicit 0.0 is complete
    ]
    res_comp = prepare_daily_series(pd.DataFrame(data_complete))
    assert res_comp["revenue_complete"] is True
    assert res_comp["series"][0]["revenue"] == 300.0
    assert res_comp["series"][1]["revenue"] == 0.0

    # Case B: Untracked revenue (no revenue column or all null)
    data_untracked = [
        {"date": "2026-08-01", "spend": 100.0},
        {"date": "2026-08-02", "spend": 100.0},
    ]
    res_untracked = prepare_daily_series(pd.DataFrame(data_untracked))
    assert res_untracked["revenue_complete"] is False
    assert res_untracked["series"][0]["revenue"] is None
    assert res_untracked["series"][1]["revenue"] is None

    # Case C: Partially missing revenue
    data_partial = [
        {"date": "2026-08-01", "spend": 100.0, "revenue": 300.0},
        {"date": "2026-08-02", "spend": 100.0, "revenue": None},
    ]
    res_partial = prepare_daily_series(pd.DataFrame(data_partial))
    assert res_partial["revenue_complete"] is False
    assert res_partial["series"][0]["revenue"] == 300.0
    assert res_partial["series"][1]["revenue"] is None

    # Case D: Invalid non-numeric revenue string
    data_invalid = [
        {"date": "2026-08-01", "spend": 100.0, "revenue": 300.0},
        {"date": "2026-08-02", "spend": 100.0, "revenue": "invalid_rev"},
    ]
    res_invalid = prepare_daily_series(pd.DataFrame(data_invalid))
    assert res_invalid["revenue_complete"] is False
    assert res_invalid["series"][0]["revenue"] == 300.0
    assert res_invalid["series"][1]["revenue"] is None


def test_deterministic_repeated_calls():
    """11. Deterministic output across repeated calls."""
    data = [
        {"date": "2026-08-03", "spend": 300.0, "conversions": 30},
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10},
        {"date": "2026-08-02", "spend": 200.0, "conversions": 20},
    ]
    df = pd.DataFrame(data)
    res1 = prepare_daily_series(df)
    res2 = prepare_daily_series(df)
    res_pkg = package_entrypoint(df)

    assert res1 == res2 == res_pkg


def test_caller_dataframe_immutability():
    """12. Caller DataFrame is not mutated in values, columns, or index."""
    data = [
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10, "revenue": 200.0},
        {"date": "invalid", "spend": 50.0, "conversions": 5, "revenue": None},
    ]
    df = pd.DataFrame(data)
    df_copy = df.copy(deep=True)

    prepare_daily_series(df)
    pd.testing.assert_frame_equal(df, df_copy)


def test_strict_json_serialization_allow_nan_false():
    """13. Output passes strict json.dumps with allow_nan=False."""
    data = [
        {"date": "2026-08-01", "spend": 0.0, "conversions": 0, "revenue": None},
        {"date": "2026-08-02", "spend": 100.0, "conversions": 10, "revenue": 200.0},
    ]
    df = pd.DataFrame(data)
    result = prepare_daily_series(df)

    serialized = json.dumps(result, allow_nan=False)
    deserialized = json.loads(serialized)
    assert deserialized["is_available"] is True
    assert len(deserialized["series"]) == 2


def test_regression_phase_1_to_3_analytics_unchanged():
    """14. Phase 1-3 analytics contracts remain completely unchanged."""
    data = [
        {"campaign_name": "Camp A", "date": "2026-08-01", "spend": 100.0, "conversions": 10, "revenue": 200.0, "customer_segment": "SMB"},
        {"campaign_name": "Camp B", "date": "2026-08-02", "spend": 200.0, "conversions": 20, "revenue": 400.0, "customer_segment": "Enterprise"},
    ]
    df = pd.DataFrame(data)

    # Phase 1 KPIs
    kpis = calculate_kpis(df)
    assert kpis["total_spend"] == 300.0
    assert kpis["total_conversions"] == 30
    assert kpis["total_revenue"] == 600.0

    # Phase 2.1 Rankings
    rankings = rank_campaigns(df)
    assert len(rankings["top"]) > 0

    # Phase 2.2 Trends
    trends = analyze_trends(df)
    assert trends["time_series"]["has_time_series"] is True

    # Phase 3.1 Cohorts
    cohorts = classify_campaign_cohorts(df)
    assert cohorts["summary"]["total_campaigns"] == 2

    # Phase 3.2 Portfolio Profiling
    portfolio = profile_segment_portfolio(df)
    assert portfolio["is_available"] is True
    assert portfolio["total_segments"] == 2


def test_seasonal_dates_diagnostic_14_contiguous_days():
    """15. has_seasonal_dates flag is True when contiguous streak >= 14."""
    data = [
        {"date": f"2026-08-{i:02d}", "spend": 100.0, "conversions": 10}
        for i in range(1, 15)
    ]
    df = pd.DataFrame(data)
    result = prepare_daily_series(df)

    assert result["is_available"] is True
    assert result["status"] == "ready"
    assert result["metadata"]["historical_dates_count"] == 14
    assert result["metadata"]["contiguous_dates_count"] == 14
    assert result["metadata"]["has_minimum_dates"] is True
    assert result["metadata"]["has_seasonal_dates"] is True
