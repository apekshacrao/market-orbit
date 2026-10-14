import json
import numpy as np
import pandas as pd
import pytest

from analytics.forecasting.data_prep import prepare_daily_series
from analytics.forecasting.baselines import forecast_baselines
from analytics.forecasting.validation import validate_baselines
from analytics.forecasting import (
    prepare_daily_series as package_entrypoint,
    forecast_baselines as package_forecast,
    validate_baselines as package_validate,
)
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
    """9. Optional clicks and impressions aggregation under Phase 4.2.1 missing-vs-zero semantics.

    Correction rationale:
    Previously, omitted clicks and impressions columns silently defaulted to integer 0,
    conflating untracked/missing metrics with legitimate observed zero activity. Under
    Phase 4.2.1 hardening, omitted metrics evaluate to None, while explicit zeros are preserved as 0.
    """
    # Clicks and impressions omitted -> None
    data_no_ci = [
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10},
    ]
    res_no_ci = prepare_daily_series(pd.DataFrame(data_no_ci))
    assert res_no_ci["series"][0]["clicks"] is None
    assert res_no_ci["series"][0]["impressions"] is None
    assert res_no_ci["metadata"]["metric_availability"]["clicks"] == "untracked"
    assert res_no_ci["metadata"]["metric_availability"]["impressions"] == "untracked"

    # Explicit observed zeros -> preserved as integer 0
    data_zero_ci = [
        {"date": "2026-08-01", "spend": 100.0, "conversions": 10, "clicks": 0, "impressions": 0},
    ]
    res_zero = prepare_daily_series(pd.DataFrame(data_zero_ci))
    assert res_zero["series"][0]["clicks"] == 0
    assert res_zero["series"][0]["impressions"] == 0
    assert res_zero["metadata"]["metric_availability"]["clicks"] == "complete"
    assert res_zero["metadata"]["metric_availability"]["impressions"] == "complete"

    # Clicks and impressions populated with valid counts
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


def test_naive_persistence_values_and_dates():
    """16. Naive persistence uses latest observed values for exact horizon dates."""
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0 + i, "conversions": 10 + i, "clicks": 50 + i, "impressions": 1000 + i, "revenue": 300.0 + i}
        for i in range(1, 8)
    ]
    df = pd.DataFrame(data)
    result = forecast_baselines(df, horizon=3)

    assert result["is_available"] is True
    assert result["horizon"] == 3
    naive = result["models"]["naive"]
    assert naive["is_eligible"] is True

    forecast = naive["forecast"]
    assert len(forecast) == 3
    assert forecast[0]["date"] == "2026-08-08"
    assert forecast[1]["date"] == "2026-08-09"
    assert forecast[2]["date"] == "2026-08-10"

    # All points equal latest observed values (day 7: spend 107.0, conv 17, clicks 57, imp 1007, rev 307.0)
    for point in forecast:
        assert point["spend"] == 107.0
        assert point["conversions"] == 17
        assert point["clicks"] == 57
        assert point["impressions"] == 1007
        assert point["revenue"] == 307.0


def test_sma_7_eligibility_and_exact_calculations():
    """17. SMA-7 calculates exact 7-day rolling mean for all additive metrics."""
    # 7 contiguous days with spend 70, 80, 90, 100, 110, 120, 130 -> sum = 700 -> avg = 100.0
    # Conversions: 7, 8, 9, 10, 11, 12, 13 -> sum = 70 -> avg = 10
    # Clicks: 35, 40, 45, 50, 55, 60, 65 -> sum = 350 -> avg = 50
    # Impressions: 700, 800, 900, 1000, 1100, 1200, 1300 -> sum = 7000 -> avg = 1000
    # Revenue: 210, 240, 270, 300, 330, 360, 390 -> sum = 2100 -> avg = 300.0
    data = [
        {
            "date": f"2026-08-0{i}",
            "spend": float(i * 10 + 60),
            "conversions": i + 6,
            "clicks": (i + 6) * 5,
            "impressions": (i * 10 + 60) * 10,
            "revenue": float((i * 10 + 60) * 3),
        }
        for i in range(1, 8)
    ]
    df = pd.DataFrame(data)
    result = forecast_baselines(df, horizon=4)

    assert result["is_available"] is True
    sma = result["models"]["sma_7"]
    assert sma["is_eligible"] is True
    assert len(sma["forecast"]) == 4

    for point in sma["forecast"]:
        assert point["spend"] == 100.0
        assert point["conversions"] == 10
        assert point["clicks"] == 50
        assert point["impressions"] == 1000
        assert point["revenue"] == 300.0


def test_seasonal_naive_eligibility_14_contiguous_dates():
    """18. Seasonal naive is eligible with 14 contiguous dates and matches prior week cycle."""
    # 14 contiguous days from Aug 1 to Aug 14
    data = [
        {
            "date": f"2026-08-{i:02d}",
            "spend": float(100 + i * 10),
            "conversions": i,
            "clicks": i * 5,
            "impressions": i * 100,
            "revenue": float(200 + i * 20),
        }
        for i in range(1, 15)
    ]
    df = pd.DataFrame(data)
    result = forecast_baselines(df, horizon=8)

    assert result["is_available"] is True
    snaive = result["models"]["seasonal_naive"]
    assert snaive["is_eligible"] is True
    assert snaive["ineligibility_reason"] is None

    forecast = snaive["forecast"]
    assert len(forecast) == 8

    # Day 1 of forecast (2026-08-15) must match Day 8 (2026-08-08, spend 180.0, conv 8)
    assert forecast[0]["date"] == "2026-08-15"
    assert forecast[0]["spend"] == 180.0
    assert forecast[0]["conversions"] == 8

    # Day 7 of forecast (2026-08-21) must match Day 14 (2026-08-14, spend 240.0, conv 14)
    assert forecast[6]["date"] == "2026-08-21"
    assert forecast[6]["spend"] == 240.0
    assert forecast[6]["conversions"] == 14

    # Day 8 of forecast (2026-08-22, wrap around) must match Day 8 (2026-08-08, spend 180.0, conv 8)
    assert forecast[7]["date"] == "2026-08-22"
    assert forecast[7]["spend"] == 180.0
    assert forecast[7]["conversions"] == 8


def test_seasonal_naive_rejection_of_14_rows_with_calendar_gaps():
    """19. Seasonal naive is declined when 14 observed rows contain calendar gaps."""
    # 14 rows spanning 16 calendar days (Aug 1-7 and Aug 10-16; missing Aug 8, Aug 9)
    dates_part1 = [f"2026-08-0{i}" for i in range(1, 8)]
    dates_part2 = [f"2026-08-{i:02d}" for i in range(10, 17)]
    data = [
        {"date": d, "spend": 100.0, "conversions": 10}
        for d in dates_part1 + dates_part2
    ]
    assert len(data) == 14

    df = pd.DataFrame(data)
    result = forecast_baselines(df, horizon=7)

    assert result["is_available"] is True
    snaive = result["models"]["seasonal_naive"]
    assert snaive["is_eligible"] is False
    assert "calendar gaps" in snaive["ineligibility_reason"].lower()
    assert snaive["forecast"] == []

    # But naive and sma_7 are still eligible
    assert result["models"]["naive"]["is_eligible"] is True
    assert result["models"]["sma_7"]["is_eligible"] is True


def test_baselines_empty_input_missing_date_and_insufficient_history():
    """20. Handles empty input, missing date column, and insufficient history deterministically."""
    # Empty DataFrame
    res_empty = forecast_baselines(pd.DataFrame(), horizon=7)
    assert res_empty["is_available"] is False
    assert res_empty["status"] == "unavailable"

    # None DataFrame
    res_none = forecast_baselines(None, horizon=7)
    assert res_none["is_available"] is False

    # Missing date column
    res_no_date = forecast_baselines(pd.DataFrame([{"spend": 100.0}]), horizon=7)
    assert res_no_date["is_available"] is False

    # Insufficient history: 4 dates (< 7)
    data_short = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10}
        for i in range(1, 5)
    ]
    res_short = forecast_baselines(pd.DataFrame(data_short), horizon=7)
    assert res_short["is_available"] is False
    assert res_short["status"] == "insufficient_history"
    assert res_short["metadata"]["historical_dates_count"] == 4
    for model in res_short["models"].values():
        assert model["is_eligible"] is False
        assert model["forecast"] == []


def test_baselines_revenue_semantics_complete_untracked_partial_invalid():
    """21. Revenue forecasts are null when revenue is incomplete, untracked, or invalid."""
    # Complete revenue
    data_comp = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10, "revenue": 300.0}
        for i in range(1, 8)
    ]
    res_comp = forecast_baselines(pd.DataFrame(data_comp), horizon=3)
    assert res_comp["revenue_complete"] is True
    assert res_comp["models"]["naive"]["forecast"][0]["revenue"] == 300.0
    assert res_comp["models"]["sma_7"]["forecast"][0]["revenue"] == 300.0

    # Untracked revenue (no column)
    data_untracked = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10}
        for i in range(1, 8)
    ]
    res_untracked = forecast_baselines(pd.DataFrame(data_untracked), horizon=3)
    assert res_untracked["revenue_complete"] is False
    assert res_untracked["models"]["naive"]["forecast"][0]["revenue"] is None
    assert res_untracked["models"]["sma_7"]["forecast"][0]["revenue"] is None
    assert any("Revenue forecasting is unavailable" in w for w in res_untracked["warnings"])

    # Partially missing revenue (one day has None)
    data_partial = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10, "revenue": 300.0 if i < 7 else None}
        for i in range(1, 8)
    ]
    res_partial = forecast_baselines(pd.DataFrame(data_partial), horizon=3)
    assert res_partial["revenue_complete"] is False
    assert res_partial["models"]["naive"]["forecast"][0]["revenue"] is None
    assert res_partial["models"]["sma_7"]["forecast"][0]["revenue"] is None

    # Invalid revenue string
    data_invalid = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10, "revenue": 300.0 if i < 7 else "corrupted"}
        for i in range(1, 8)
    ]
    res_invalid = forecast_baselines(pd.DataFrame(data_invalid), horizon=3)
    assert res_invalid["revenue_complete"] is False
    assert res_invalid["models"]["naive"]["forecast"][0]["revenue"] is None


def test_baselines_observed_zero_vs_unresolved_gaps():
    """22. Preserves observed zeros in latest observation without zero-filling gaps."""
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10}
        for i in range(1, 7)
    ]
    # Day 7 has observed zero spend and conversions
    data.append({"date": "2026-08-07", "spend": 0.0, "conversions": 0})
    df = pd.DataFrame(data)
    result = forecast_baselines(df, horizon=2)

    naive_forecast = result["models"]["naive"]["forecast"]
    assert naive_forecast[0]["spend"] == 0.0
    assert naive_forecast[0]["conversions"] == 0


def test_baselines_optional_clicks_impressions():
    """23. Omitted clicks and impressions forecast as None with unavailable status.

    Correction rationale:
    Previously, omitted clicks and impressions were silently defaulted to 0 in baseline
    forecasts. Under Phase 4.2.1 contract hardening, absent metrics produce None (JSON null)
    and metric_status='unavailable' to avoid misleading users with synthetic zero forecasts.
    """
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10}
        for i in range(1, 8)
    ]
    result = forecast_baselines(pd.DataFrame(data), horizon=3)
    for model in ["naive", "sma_7"]:
        m_dict = result["models"][model]
        assert m_dict["metric_status"]["clicks"] == "unavailable"
        assert m_dict["metric_status"]["impressions"] == "unavailable"
        assert m_dict["metric_status"]["spend"] == "available"
        assert m_dict["metric_status"]["conversions"] == "available"
        fc = m_dict["forecast"]
        for pt in fc:
            assert pt["clicks"] is None
            assert pt["impressions"] is None
            assert pt["spend"] == 100.0
            assert pt["conversions"] == 10


def test_baselines_invalid_horizon_rejection():
    """24. Rejects invalid horizon values (0, negative, booleans, strings, floats) with ValueError."""
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10}
        for i in range(1, 8)
    ]
    df = pd.DataFrame(data)

    invalid_horizons = [0, -1, -7, True, False, "7", "seven", 7.5, 0.0, None]
    for h in invalid_horizons:
        with pytest.raises(ValueError):
            forecast_baselines(df, horizon=h)


def test_baselines_deterministic_repeated_calls():
    """25. Repeated calls produce identical output dictionaries."""
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0 * i, "conversions": 5 * i}
        for i in range(1, 8)
    ]
    df = pd.DataFrame(data)
    res1 = forecast_baselines(df, horizon=5)
    res2 = forecast_baselines(df, horizon=5)
    res_pkg = package_forecast(df, horizon=5)

    assert res1 == res2 == res_pkg


def test_baselines_caller_dataframe_immutability():
    """26. Caller DataFrame is not mutated in values, columns, or index."""
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10, "revenue": 200.0}
        for i in range(1, 8)
    ]
    df = pd.DataFrame(data)
    df_copy = df.copy(deep=True)

    forecast_baselines(df, horizon=7)
    pd.testing.assert_frame_equal(df, df_copy)


def test_baselines_strict_json_serialization_allow_nan_false():
    """27. Forecast results pass strict json.dumps with allow_nan=False."""
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10, "revenue": None}
        for i in range(1, 8)
    ]
    df = pd.DataFrame(data)
    result = forecast_baselines(df, horizon=7)

    serialized = json.dumps(result, allow_nan=False)
    deserialized = json.loads(serialized)
    assert deserialized["is_available"] is True
    assert "naive" in deserialized["models"]
    assert "sma_7" in deserialized["models"]


def test_duplicate_date_revenue_uncertainty_preservation():
    """28. Duplicate records on the same date preserve revenue uncertainty."""
    # On 2026-08-01: Row 1 has revenue 100.0, Row 2 has revenue None -> date revenue must be None
    data_partial_dup = [
        {"date": "2026-08-01", "spend": 50.0, "conversions": 5, "revenue": 100.0},
        {"date": "2026-08-01", "spend": 50.0, "conversions": 5, "revenue": None},
    ]
    res_dup = prepare_daily_series(pd.DataFrame(data_partial_dup))
    assert res_dup["revenue_complete"] is False
    assert res_dup["series"][0]["revenue"] is None

    # On 2026-08-01: Row 1 has revenue 100.0, Row 2 has revenue 'invalid_rev' -> date revenue must be None
    data_invalid_dup = [
        {"date": "2026-08-01", "spend": 50.0, "conversions": 5, "revenue": 100.0},
        {"date": "2026-08-01", "spend": 50.0, "conversions": 5, "revenue": "invalid_rev"},
    ]
    res_inv_dup = prepare_daily_series(pd.DataFrame(data_invalid_dup))
    assert res_inv_dup["revenue_complete"] is False
    assert res_inv_dup["series"][0]["revenue"] is None

    # On 2026-08-01: Row 1 has revenue 100.0, Row 2 has revenue 200.0 -> date revenue is 300.0
    data_valid_dup = [
        {"date": "2026-08-01", "spend": 50.0, "conversions": 5, "revenue": 100.0},
        {"date": "2026-08-01", "spend": 50.0, "conversions": 5, "revenue": 200.0},
    ]
    res_valid_dup = prepare_daily_series(pd.DataFrame(data_valid_dup))
    assert res_valid_dup["revenue_complete"] is True
    assert res_valid_dup["series"][0]["revenue"] == 300.0


def test_sma_7_rejection_on_window_calendar_gaps():
    """29. SMA-7 is rejected when calendar gaps exist in the 7-day baseline window."""
    # 7 distinct observed dates spanning 8 calendar days (Aug 1 to 6, then Aug 8; Aug 7 missing)
    dates = ["2026-08-01", "2026-08-02", "2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-08"]
    data = [
        {"date": d, "spend": 100.0, "conversions": 10, "clicks": 50, "impressions": 1000}
        for d in dates
    ]
    df = pd.DataFrame(data)
    result = forecast_baselines(df, horizon=3)

    assert result["is_available"] is True
    sma = result["models"]["sma_7"]
    # Under Phase 4.2.1, SMA-7 strictly requires 7 consecutive calendar dates
    assert sma["is_eligible"] is False
    assert sma["forecast"] == []
    assert "calendar gaps" in sma["ineligibility_reason"].lower()
    for m in ["spend", "conversions", "clicks", "impressions", "revenue"]:
        assert sma["metric_status"][m] == "ineligible"

    # Naive persistence remains eligible because it only requires the latest observation
    naive = result["models"]["naive"]
    assert naive["is_eligible"] is True
    assert len(naive["forecast"]) == 3
    assert naive["forecast"][0]["date"] == "2026-08-09"
    assert naive["forecast"][0]["spend"] == 100.0


def test_sma_7_metric_specific_unusable_observations():
    """30. SMA-7 marks individual unusable metrics unavailable while keeping valid metrics available."""
    # 7 contiguous calendar days (Aug 1 to Aug 7)
    # Spend & Conversions: valid on all 7 days
    # Clicks: missing (None) on Aug 4
    # Impressions: corrupted string on Aug 7
    # Revenue: untracked
    data = []
    for i in range(1, 8):
        rec = {
            "date": f"2026-08-0{i}",
            "spend": 100.0,
            "conversions": 10,
            "clicks": 50 if i != 4 else None,
            "impressions": 1000 if i != 7 else "corrupted",
        }
        data.append(rec)

    df = pd.DataFrame(data)
    result = forecast_baselines(df, horizon=2)

    assert result["is_available"] is True
    sma = result["models"]["sma_7"]
    assert sma["is_eligible"] is True  # 7 calendar days are contiguous
    assert sma["ineligibility_reason"] is None

    # Status breakdown per metric
    assert sma["metric_status"]["spend"] == "available"
    assert sma["metric_status"]["conversions"] == "available"
    assert sma["metric_status"]["clicks"] == "unavailable"
    assert sma["metric_status"]["impressions"] == "unavailable"
    assert sma["metric_status"]["revenue"] == "unavailable"

    assert sma["metric_reasons"]["clicks"] is not None
    assert "unavailable" in sma["metric_reasons"]["clicks"].lower()

    # Forecast values: valid metrics computed, unavailable metrics strictly None
    for pt in sma["forecast"]:
        assert pt["spend"] == 100.0
        assert pt["conversions"] == 10
        assert pt["clicks"] is None
        assert pt["impressions"] is None
        assert pt["revenue"] is None

    # Check diagnostic warnings
    warnings_text = " ".join(result["warnings"])
    assert "clicks" in warnings_text.lower()
    assert "impressions" in warnings_text.lower()


def test_count_metric_validation_negative_fractional_non_finite_booleans():
    """31. Count metric validation rejects negative, fractional, non-finite, and boolean observations."""
    data = [
        {"date": "2026-08-01", "spend": 100.0, "conversions": -5},                 # negative count -> None
        {"date": "2026-08-02", "spend": 100.0, "clicks": 12.5},                     # fractional count -> None
        {"date": "2026-08-03", "spend": 100.0, "impressions": float("inf")},         # non-finite count -> None
        {"date": "2026-08-04", "spend": 100.0, "conversions": True},                # boolean -> None
        {"date": "2026-08-05", "spend": 100.0, "clicks": "ten"},                    # string unparseable -> None
        {"date": "2026-08-06", "spend": 0.0, "clicks": 0, "conversions": 0, "impressions": 0},  # explicit 0 -> 0
        {"date": "2026-08-07", "spend": 100.0, "clicks": 10, "conversions": 5, "impressions": 100},  # valid count
    ]
    df = pd.DataFrame(data)
    result = prepare_daily_series(df)

    assert result["is_available"] is True
    s = result["series"]

    # Day 1: negative conversions rejected
    assert s[0]["conversions"] is None
    # Day 2: fractional clicks rejected
    assert s[1]["clicks"] is None
    # Day 3: non-finite impressions rejected
    assert s[2]["impressions"] is None
    # Day 4: boolean conversions rejected
    assert s[3]["conversions"] is None
    # Day 5: unparseable string clicks rejected
    assert s[4]["clicks"] is None
    # Day 6: explicit zeros preserved
    assert s[5]["spend"] == 0.0
    assert s[5]["clicks"] == 0
    assert s[5]["conversions"] == 0
    assert s[5]["impressions"] == 0
    # Day 7: valid numbers preserved
    assert s[6]["clicks"] == 10
    assert s[6]["conversions"] == 5
    assert s[6]["impressions"] == 100


def test_sma_7_count_rounding_policy_explicit_verification():
    """32. SMA-7 count metric rounding produces non-negative integers via standard round-half-to-even."""
    # Case A: sum = 73 -> mean = 73/7 = 10.42857 -> round to 10
    data_a = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10 if i < 7 else 13}
        for i in range(1, 8)
    ]
    res_a = forecast_baselines(pd.DataFrame(data_a), horizon=1)
    pt_a = res_a["models"]["sma_7"]["forecast"][0]
    assert pt_a["conversions"] == 10
    assert isinstance(pt_a["conversions"], int)

    # Case B: sum = 74 -> mean = 74/7 = 10.57143 -> round to 11
    data_b = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10 if i < 7 else 14}
        for i in range(1, 8)
    ]
    res_b = forecast_baselines(pd.DataFrame(data_b), horizon=1)
    pt_b = res_b["models"]["sma_7"]["forecast"][0]
    assert pt_b["conversions"] == 11
    assert isinstance(pt_b["conversions"], int)

    # Case C: sum = 1 -> mean = 1/7 = 0.142857 -> round to 0
    data_c = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 0 if i < 7 else 1}
        for i in range(1, 8)
    ]
    res_c = forecast_baselines(pd.DataFrame(data_c), horizon=1)
    pt_c = res_c["models"]["sma_7"]["forecast"][0]
    assert pt_c["conversions"] == 0
    assert isinstance(pt_c["conversions"], int)

    # Case D: sum = 4 -> mean = 4/7 = 0.571429 -> round to 1
    data_d = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 0 if i < 4 else 1}
        for i in range(1, 8)
    ]
    res_d = forecast_baselines(pd.DataFrame(data_d), horizon=1)
    pt_d = res_d["models"]["sma_7"]["forecast"][0]
    assert pt_d["conversions"] == 1
    assert isinstance(pt_d["conversions"], int)


def test_seasonal_naive_metric_specific_unavailability():
    """33. Seasonal naive marks metric unavailable if any observation in the 7-day cycle is unusable."""
    # 14 contiguous days from Aug 1 to Aug 14
    # Spend and clicks valid across all 14 days
    # Conversions has None on Aug 10 (day 10, within the 7-day seasonal cycle)
    data = [
        {
            "date": f"2026-08-{i:02d}",
            "spend": float(100 + i * 10),
            "conversions": i if i != 10 else None,
            "clicks": i * 5,
            "impressions": i * 100,
        }
        for i in range(1, 15)
    ]
    df = pd.DataFrame(data)
    result = forecast_baselines(df, horizon=7)

    assert result["is_available"] is True
    snaive = result["models"]["seasonal_naive"]
    assert snaive["is_eligible"] is True

    # Spend & clicks available; conversions unavailable
    assert snaive["metric_status"]["spend"] == "available"
    assert snaive["metric_status"]["clicks"] == "available"
    assert snaive["metric_status"]["impressions"] == "available"
    assert snaive["metric_status"]["conversions"] == "unavailable"

    forecast = snaive["forecast"]
    assert len(forecast) == 7
    for pt in forecast:
        assert pt["spend"] is not None
        assert pt["clicks"] is not None
        assert pt["conversions"] is None  # Unavailable metric forecasts as None


def test_negative_spend_and_currency_validation():
    """34. Currency validation rejects negative and non-finite spend values."""
    data = [
        {"date": "2026-08-01", "spend": -100.0, "conversions": 10},  # negative spend -> None
        {"date": "2026-08-02", "spend": float("nan"), "conversions": 10},  # nan spend -> None
        {"date": "2026-08-03", "spend": 0.0, "conversions": 10},  # explicit 0.0 -> 0.0
    ]
    res = prepare_daily_series(pd.DataFrame(data))
    assert res["is_available"] is True
    assert res["series"][0]["spend"] is None
    assert res["series"][1]["spend"] is None
    assert res["series"][2]["spend"] == 0.0


def test_full_json_serialization_with_null_and_zero_metrics():
    """35. Strict JSON serialization handles mixed null, zero, and active metric forecasts."""
    # Mix of active, zero, and untracked metrics
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 0, "clicks": None}
        for i in range(1, 8)
    ]
    df = pd.DataFrame(data)
    result = forecast_baselines(df, horizon=5)

    # Must serialize without error under allow_nan=False
    raw_json = json.dumps(result, allow_nan=False)
    parsed = json.loads(raw_json)

    # Verify JSON literal types
    assert parsed["is_available"] is True
    for model_name in ["naive", "sma_7"]:
        fc = parsed["models"][model_name]["forecast"]
        for pt in fc:
            assert pt["spend"] == 100.0
            assert pt["conversions"] == 0   # literal integer 0
            assert pt["clicks"] is None      # literal JSON null
            assert pt["revenue"] is None     # literal JSON null


def test_walk_forward_hand_calculable_metrics():
    """36. Hand-calculable walk-forward validation with exact MAE, RMSE, and WAPE."""
    # 9 contiguous days from Aug 1 to Aug 9
    # spend: 100, 110, 120, 130, 140, 150, 160, 170, 180
    # conversions: 10, 11, 12, 13, 14, 15, 16, 17, 18
    data = [
        {
            "date": f"2026-08-0{i}",
            "spend": float(100 + (i - 1) * 10),
            "conversions": 10 + (i - 1),
        }
        for i in range(1, 10)
    ]
    df = pd.DataFrame(data)

    # horizon=2, min_train_dates=7, step=1
    # Total dates = 9
    # Origin 1: k=6 (Aug 7) -> train Aug 1..7 (7 dates), forecast Aug 8 & Aug 9. Both observed.
    # Origin 2: k=7 (Aug 8) -> train Aug 1..8 (8 dates), forecast Aug 9 & Aug 10. Only Aug 9 observed.
    # Total evaluated forecast points = 3 points.
    res = validate_baselines(df, horizon=2, min_train_dates=7, step=1)

    assert res["is_available"] is True
    assert res["status"] == "ready"
    assert res["parameters"]["horizon"] == 2
    assert res["parameters"]["min_train_dates"] == 7
    assert res["parameters"]["step"] == 1

    meta = res["metadata"]
    assert meta["total_origins_generated"] == 2
    assert len(meta["origins"]) == 2
    assert meta["origins"][0]["origin_date"] == "2026-08-07"
    assert meta["origins"][0]["observed_eval_dates_count"] == 2
    assert meta["origins"][1]["origin_date"] == "2026-08-08"
    assert meta["origins"][1]["observed_eval_dates_count"] == 1

    # Naive baseline evaluation:
    # Origin 1 (Aug 7 latest: spend=160, conv=16):
    #   Aug 8 actual: spend=170, conv=17 -> abs_err=10, sq_err=100
    #   Aug 9 actual: spend=180, conv=18 -> abs_err=20, sq_err=400
    # Origin 2 (Aug 8 latest: spend=170, conv=17):
    #   Aug 9 actual: spend=180, conv=18 -> abs_err=10, sq_err=100
    # Spend: sum_abs=40.0, sum_sq=600.0, sum_actual=530.0, count=3
    #   MAE = 40/3 = 13.3333
    #   RMSE = sqrt(600/3) = sqrt(200) = 14.1421
    #   WAPE = (40 / 530) * 100 = 7.5472%
    # Conversions: sum_abs=4, sum_sq=6, sum_actual=53, count=3
    #   MAE = 4/3 = 1.3333
    #   RMSE = sqrt(6/3) = sqrt(2) = 1.4142
    #   WAPE = (4 / 53) * 100 = 7.5472%
    naive = res["models"]["naive"]
    assert naive["origins_eligible"] == 2
    assert naive["origins_ineligible"] == 0

    spend_naive = naive["metrics"]["spend"]
    assert spend_naive["points_evaluated"] == 3
    assert spend_naive["mae"] == 13.3333
    assert spend_naive["rmse"] == 14.1421
    assert spend_naive["wape"] == 7.5472
    assert spend_naive["wape_status"] == "available"

    conv_naive = naive["metrics"]["conversions"]
    assert conv_naive["points_evaluated"] == 3
    assert conv_naive["mae"] == 1.3333
    assert conv_naive["rmse"] == 1.4142
    assert conv_naive["wape"] == 7.5472

    # SMA-7 baseline evaluation:
    # Origin 1 (Aug 1..7 avg: spend=130, conv=13):
    #   Aug 8 actual: spend=170, conv=17 -> abs_err=40, sq_err=1600
    #   Aug 9 actual: spend=180, conv=18 -> abs_err=50, sq_err=2500
    # Origin 2 (Aug 2..8 avg: spend=140, conv=14):
    #   Aug 9 actual: spend=180, conv=18 -> abs_err=40, sq_err=1600
    # Spend: sum_abs=130.0, sum_sq=5700.0, sum_actual=530.0, count=3
    #   MAE = 130/3 = 43.3333
    #   RMSE = sqrt(5700/3) = sqrt(1900) = 43.5890
    #   WAPE = (130 / 530) * 100 = 24.5283%
    # Conversions: sum_abs=13, sum_sq=57, sum_actual=53, count=3
    #   MAE = 13/3 = 4.3333
    #   RMSE = sqrt(57/3) = sqrt(19) = 4.3589
    #   WAPE = (13 / 53) * 100 = 24.5283%
    sma = res["models"]["sma_7"]
    assert sma["origins_eligible"] == 2
    assert sma["origins_ineligible"] == 0

    spend_sma = sma["metrics"]["spend"]
    assert spend_sma["points_evaluated"] == 3
    assert spend_sma["mae"] == 43.3333
    assert spend_sma["rmse"] == 43.5890
    assert spend_sma["wape"] == 24.5283

    conv_sma = sma["metrics"]["conversions"]
    assert conv_sma["points_evaluated"] == 3
    assert conv_sma["mae"] == 4.3333
    assert conv_sma["rmse"] == 4.3589
    assert conv_sma["wape"] == 24.5283

    # Seasonal naive is ineligible because training history is < 14 dates at both origins
    snaive = res["models"]["seasonal_naive"]
    assert snaive["origins_eligible"] == 0
    assert snaive["origins_ineligible"] == 2
    assert any("requires at least 14" in r for r in snaive["ineligibility_reasons"])
    assert snaive["metrics"]["spend"]["points_evaluated"] == 0
    assert snaive["metrics"]["spend"]["mae"] is None


def test_walk_forward_seasonal_naive_eligibility_and_calculation():
    """37. Seasonal naive becomes eligible when training split reaches 14 contiguous dates."""
    # 16 contiguous days from Aug 1 to Aug 16
    data = [
        {
            "date": f"2026-08-{i:02d}",
            "spend": float(100 + i * 10),
            "conversions": i,
        }
        for i in range(1, 17)
    ]
    df = pd.DataFrame(data)

    # min_train_dates=14, horizon=2, step=1
    # Origin 1: k=13 (Aug 14) -> train Aug 1..14 (14 dates), forecast Aug 15 & 16 (both observed)
    # Origin 2: k=14 (Aug 15) -> train Aug 1..15 (15 dates), forecast Aug 16 & 17 (only Aug 16 observed)
    res = validate_baselines(df, horizon=2, min_train_dates=14, step=1)

    assert res["is_available"] is True
    snaive = res["models"]["seasonal_naive"]
    assert snaive["origins_eligible"] == 2
    assert snaive["origins_ineligible"] == 0

    spend_snaive = snaive["metrics"]["spend"]
    assert spend_snaive["points_evaluated"] == 3
    assert spend_snaive["mae"] is not None
    assert spend_snaive["rmse"] is not None
    assert spend_snaive["wape"] is not None


def test_walk_forward_leakage_safety_future_isolation():
    """38. Future records never leak into earlier training windows or influence earlier forecasts."""
    # Base dataset: 10 days
    data_base = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10}
        for i in range(1, 10)
    ]
    data_base.append({"date": "2026-08-10", "spend": 100.0, "conversions": 10})

    # Tampered dataset: day 10 has a massive budget spike of 50,000
    data_tampered = [dict(r) for r in data_base]
    data_tampered[-1]["spend"] = 50000.0

    res_base = validate_baselines(pd.DataFrame(data_base), horizon=2, min_train_dates=7, step=1)
    res_tampered = validate_baselines(pd.DataFrame(data_tampered), horizon=2, min_train_dates=7, step=1)

    # Origin 1 is at 2026-08-07 (evaluating Aug 8 and Aug 9)
    # Both datasets have identical data up to Aug 7, so forecasts made at Origin 1 MUST be identical!
    orig_base_1 = res_base["metadata"]["origins"][0]
    orig_tamp_1 = res_tamp = res_tampered["metadata"]["origins"][0]
    assert orig_base_1["train_dates_count"] == orig_tamp_1["train_dates_count"] == 7
    assert orig_base_1["forecast_start_date"] == orig_tamp_1["forecast_start_date"] == "2026-08-08"


def test_walk_forward_parameter_validation():
    """39. Rejects invalid horizon, min_train_dates, and step parameters."""
    df = pd.DataFrame([{"date": f"2026-08-0{i}", "spend": 100.0} for i in range(1, 9)])

    invalid_params = [0, -1, -5, True, False, "7", "seven", 7.5, None]

    for p in invalid_params:
        with pytest.raises(ValueError):
            validate_baselines(df, horizon=p)
        with pytest.raises(ValueError):
            validate_baselines(df, min_train_dates=p)
        with pytest.raises(ValueError):
            validate_baselines(df, step=p)


def test_walk_forward_insufficient_history_and_empty_inputs():
    """40. Handles empty inputs, missing date column, and insufficient history deterministically."""
    # None input
    res_none = validate_baselines(None)
    assert res_none["is_available"] is False
    assert res_none["status"] == "unavailable"

    # Empty DataFrame
    res_empty = validate_baselines(pd.DataFrame())
    assert res_empty["is_available"] is False
    assert res_empty["status"] == "unavailable"

    # Missing date column
    res_no_date = validate_baselines(pd.DataFrame([{"spend": 100.0}]))
    assert res_no_date["is_available"] is False
    assert res_no_date["status"] == "unavailable"

    # Insufficient dates: 10 dates with min_train_dates=14
    df_short = pd.DataFrame([{"date": f"2026-08-{i:02d}", "spend": 100.0} for i in range(1, 11)])
    res_short = validate_baselines(df_short, min_train_dates=14)
    assert res_short["is_available"] is False
    assert res_short["status"] == "insufficient_history"
    assert any("at least 15" in w for w in res_short["warnings"])

    # Exactly min_train_dates (14 dates) -> 0 future test dates remaining -> insufficient
    df_exact = pd.DataFrame([{"date": f"2026-08-{i:02d}", "spend": 100.0} for i in range(1, 15)])
    res_exact = validate_baselines(df_exact, min_train_dates=14)
    assert res_exact["is_available"] is False
    assert res_exact["status"] == "insufficient_history"


def test_walk_forward_calendar_gaps_and_missing_eval_dates():
    """41. Handles unobserved calendar dates in forecast horizon without fabricating actuals."""
    # Observed dates: Aug 1..7 (training), Aug 8 (observed), then gap until Aug 12 (observed)
    # Aug 9, 10, 11 are unobserved
    dates = [f"2026-08-0{i}" for i in range(1, 9)] + ["2026-08-12"]
    data = [{"date": d, "spend": 100.0, "conversions": 10} for d in dates]
    df = pd.DataFrame(data)

    # min_train_dates=7, horizon=5, step=1
    # Origin 1 at Aug 7: horizon spans Aug 8 to Aug 12 (5 days).
    # Actual observations exist ONLY for Aug 8 and Aug 12 (2 days).
    res = validate_baselines(df, horizon=5, min_train_dates=7, step=1)

    assert res["is_available"] is True
    assert res["metadata"]["total_origins_generated"] == 2
    orig1 = res["metadata"]["origins"][0]
    assert orig1["origin_date"] == "2026-08-07"
    assert orig1["observed_eval_dates_count"] == 2  # Aug 8 and Aug 12 only (Aug 9-11 unobserved)

    orig2 = res["metadata"]["origins"][1]
    assert orig2["origin_date"] == "2026-08-08"
    assert orig2["observed_eval_dates_count"] == 1  # Aug 12 only in horizon Aug 9..13

    # Total forecast points evaluated for Naive across both origins: 2 + 1 = 3
    assert res["models"]["naive"]["metrics"]["spend"]["points_evaluated"] == 3


def test_walk_forward_wape_zero_denominator():
    """42. WAPE returns None with status 'undefined_zero_actuals' when sum of actuals is zero."""
    # Conversions explicitly observed as 0 across all days
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 0}
        for i in range(1, 10)
    ]
    df = pd.DataFrame(data)
    res = validate_baselines(df, horizon=2, min_train_dates=7, step=1)

    assert res["is_available"] is True
    conv_naive = res["models"]["naive"]["metrics"]["conversions"]
    assert conv_naive["points_evaluated"] == 3
    assert conv_naive["mae"] == 0.0
    assert conv_naive["rmse"] == 0.0
    # Denominator sum of actuals is 0 -> WAPE is undefined null
    assert conv_naive["wape"] is None
    assert conv_naive["wape_status"] == "undefined_zero_actuals"


def test_walk_forward_revenue_completeness():
    """43. Revenue is only evaluated when both training split and evaluation actuals satisfy completeness."""
    # Case A: Complete revenue
    data_comp = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10, "revenue": 300.0}
        for i in range(1, 10)
    ]
    res_comp = validate_baselines(pd.DataFrame(data_comp), horizon=2, min_train_dates=7, step=1)
    assert res_comp["revenue_complete"] is True
    assert res_comp["models"]["naive"]["metrics"]["revenue"]["points_evaluated"] == 3
    assert res_comp["models"]["naive"]["metrics"]["revenue"]["mae"] == 0.0

    # Case B: Untracked revenue (no column)
    data_untracked = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10}
        for i in range(1, 10)
    ]
    res_untracked = validate_baselines(pd.DataFrame(data_untracked), horizon=2, min_train_dates=7, step=1)
    assert res_untracked["revenue_complete"] is False
    rev_eval = res_untracked["models"]["naive"]["metrics"]["revenue"]
    assert rev_eval["points_evaluated"] == 0
    assert rev_eval["mae"] is None
    assert rev_eval["wape_status"] == "no_evaluated_points"

    # Case C: Partially missing revenue in training
    data_part = [dict(r) for r in data_comp]
    data_part[2]["revenue"] = None  # day 3 missing revenue -> invalidates training splits
    res_part = validate_baselines(pd.DataFrame(data_part), horizon=2, min_train_dates=7, step=1)
    assert res_part["revenue_complete"] is False
    assert res_part["models"]["naive"]["metrics"]["revenue"]["points_evaluated"] == 0


def test_walk_forward_metric_specific_evaluation_counts():
    """44. Distinguishes metric evaluation sample sizes when some metrics are untracked or partially missing."""
    # 9 days: spend & conversions on all 9 days.
    # clicks: tracked ONLY on days 5..9 (None on days 1..4)
    data = []
    for i in range(1, 10):
        data.append({
            "date": f"2026-08-0{i}",
            "spend": 100.0,
            "conversions": 10,
            "clicks": 50 if i >= 5 else None,
        })
    df = pd.DataFrame(data)
    res = validate_baselines(df, horizon=2, min_train_dates=7, step=1)

    assert res["is_available"] is True
    # Spend evaluated on all 3 test points
    assert res["models"]["naive"]["metrics"]["spend"]["points_evaluated"] == 3
    # Clicks at origin 1 (Aug 7) has clicks on Aug 7 -> forecasts 50 for Aug 8 & Aug 9 (both have actual clicks 50)
    # Clicks at origin 2 (Aug 8) has clicks on Aug 8 -> forecasts 50 for Aug 9
    assert res["models"]["naive"]["metrics"]["clicks"]["points_evaluated"] == 3

    # But for SMA-7:
    # Origin 1 (Aug 7) looks at Aug 1..7. Days 1..4 have None -> SMA-7 clicks is UNAVAILABLE!
    # Origin 2 (Aug 8) looks at Aug 2..8. Days 2..4 have None -> SMA-7 clicks is UNAVAILABLE!
    # Thus SMA-7 clicks points_evaluated is 0!
    assert res["models"]["sma_7"]["metrics"]["clicks"]["points_evaluated"] == 0
    assert res["models"]["sma_7"]["metrics"]["spend"]["points_evaluated"] == 3


def test_walk_forward_immutability_and_determinism():
    """45. Repeated calls produce identical outputs; caller DataFrame is unmutated."""
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0 + i, "conversions": 10 + i}
        for i in range(1, 10)
    ]
    df = pd.DataFrame(data)
    df_copy = df.copy(deep=True)

    res1 = validate_baselines(df, horizon=2, min_train_dates=7, step=1)
    res2 = validate_baselines(df, horizon=2, min_train_dates=7, step=1)

    # Immutability
    pd.testing.assert_frame_equal(df, df_copy)

    # Determinism
    assert res1 == res2

    # JSON serialization
    serialized = json.dumps(res1, allow_nan=False)
    deserialized = json.loads(serialized)
    assert deserialized["is_available"] is True
    assert deserialized["status"] == "ready"


def test_walk_forward_package_export():
    """46. validate_baselines is exposed via package root analytics.forecasting."""
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10}
        for i in range(1, 10)
    ]
    df = pd.DataFrame(data)
    res_direct = validate_baselines(df, horizon=2, min_train_dates=7, step=1)
    res_pkg = package_validate(df, horizon=2, min_train_dates=7, step=1)

    assert res_direct == res_pkg


def test_walk_forward_28_date_reference_case():
    """47. 28-date reference case produces exactly 14 origins and 77 evaluated points per metric."""
    # 28 consecutive calendar dates with all 5 metrics populated and valid
    data = [
        {
            "date": f"2026-08-{i:02d}",
            "spend": float(100 + i * 5),
            "conversions": 10 + (i % 5),
            "clicks": 50 + i * 2,
            "impressions": 1000 + i * 50,
            "revenue": float(300 + i * 10),
        }
        for i in range(1, 29)
    ]
    df = pd.DataFrame(data)

    # horizon=7, min_train_dates=14, step=1
    res = validate_baselines(df, horizon=7, min_train_dates=14, step=1)

    assert res["is_available"] is True
    assert res["status"] == "ready"
    assert res["revenue_complete"] is True

    # 1. Exact Origin Count Verification
    # Initial origin: k = 13 (Aug 14, 14 training dates)
    # Loop continues while k < 27 (last date Aug 28 is k=27)
    # Origins: k = 13, 14, 15, ..., 26 -> exactly 14 origins
    meta = res["metadata"]
    assert meta["total_origins_generated"] == 14
    assert len(meta["origins"]) == 14
    assert meta["origins"][0]["origin_date"] == "2026-08-14"
    assert meta["origins"][-1]["origin_date"] == "2026-08-27"

    # 2. Exact Progressive Horizon Truncation Breakdown
    # Origins 0..7 (k=13..20): full 7-day horizon inside dataset (8 * 7 = 56 points)
    for i in range(8):
        assert meta["origins"][i]["observed_eval_dates_count"] == 7
    # Origins 8..13 (k=21..26): progressively truncated horizons near dataset end
    assert meta["origins"][8]["observed_eval_dates_count"] == 6   # Aug 23..28
    assert meta["origins"][9]["observed_eval_dates_count"] == 5   # Aug 24..28
    assert meta["origins"][10]["observed_eval_dates_count"] == 4  # Aug 25..28
    assert meta["origins"][11]["observed_eval_dates_count"] == 3  # Aug 26..28
    assert meta["origins"][12]["observed_eval_dates_count"] == 2  # Aug 27..28
    assert meta["origins"][13]["observed_eval_dates_count"] == 1  # Aug 28 only

    # Total evaluated points across all 14 origins = 56 + 6 + 5 + 4 + 3 + 2 + 1 = 77 points
    expected_total_points = 56 + 21
    assert expected_total_points == 77

    # 3. Model & Metric Verification
    for model_key in ["naive", "sma_7", "seasonal_naive"]:
        m_dict = res["models"][model_key]
        assert m_dict["origins_eligible"] == 14
        assert m_dict["origins_ineligible"] == 0

        for metric in ["spend", "conversions", "clicks", "impressions", "revenue"]:
            met_eval = m_dict["metrics"][metric]
            assert met_eval["points_evaluated"] == 77
            assert met_eval["mae"] is not None
            assert met_eval["rmse"] is not None
            assert met_eval["wape"] is not None
            assert met_eval["wape_status"] == "available"


def test_walk_forward_pooled_vs_unweighted_origin_aggregation():
    """48. Verifies point-weighted pooled error aggregation over unweighted origin averages."""
    # Hand-calculable fixture with unequal points across origins:
    # 9 days from Aug 1 to Aug 9.
    # min_train_dates=7, horizon=2, step=1
    # Origin 1 (Aug 7): 2 test points (Aug 8: err=10, Aug 9: err=20) -> per-origin MAE = 15.0
    # Origin 2 (Aug 8): 1 test point (Aug 9: err=10) -> per-origin MAE = 10.0
    # If unweighted average of origins: (15.0 + 10.0) / 2 = 12.5
    # If point-weighted pooled: (10 + 20 + 10) / 3 = 40 / 3 = 13.3333
    data = [
        {"date": f"2026-08-0{i}", "spend": float(100 + (i - 1) * 10), "conversions": 10}
        for i in range(1, 10)
    ]
    df = pd.DataFrame(data)
    res = validate_baselines(df, horizon=2, min_train_dates=7, step=1)

    spend_naive = res["models"]["naive"]["metrics"]["spend"]
    assert spend_naive["points_evaluated"] == 3
    # Point-weighted pooled MAE must be 13.3333, strictly NOT the unweighted origin average 12.5
    assert spend_naive["mae"] == 13.3333
    assert spend_naive["mae"] != 12.5


def test_walk_forward_multi_origin_repeated_date_evaluation():
    """49. Verifies that the same calendar date is evaluated independently across rolling origins."""
    # 9 days: Aug 9 is in the horizon of both Origin 1 (Aug 7, h=2) and Origin 2 (Aug 8, h=1)
    data = [
        {"date": f"2026-08-0{i}", "spend": 100.0, "conversions": 10}
        for i in range(1, 10)
    ]
    df = pd.DataFrame(data)
    res = validate_baselines(df, horizon=2, min_train_dates=7, step=1)

    orig1 = res["metadata"]["origins"][0]
    orig2 = res["metadata"]["origins"][1]

    # Origin 1 (Aug 7) projects Aug 8 and Aug 9
    assert orig1["forecast_start_date"] == "2026-08-08"
    assert orig1["forecast_end_date"] == "2026-08-09"

    # Origin 2 (Aug 8) projects Aug 9 and Aug 10 (Aug 10 unobserved)
    assert orig2["forecast_start_date"] == "2026-08-09"
    assert orig2["forecast_end_date"] == "2026-08-10"

    # Aug 9 was evaluated in both origins
    assert orig1["models"]["naive"]["points_evaluated"]["spend"] == 2
    assert orig2["models"]["naive"]["points_evaluated"]["spend"] == 1


def test_walk_forward_untracked_metric_zero_points_no_scores():
    """50. Untracked metrics produce zero evaluated points and strictly null scores."""
    # Dataset with only spend and conversions; clicks, impressions, revenue untracked
    data = [
        {"date": f"2026-08-{i:02d}", "spend": 100.0, "conversions": 10}
        for i in range(1, 16)
    ]
    df = pd.DataFrame(data)
    res = validate_baselines(df, horizon=2, min_train_dates=14, step=1)

    assert res["is_available"] is True
    for model_key in ["naive", "sma_7", "seasonal_naive"]:
        for untracked_met in ["clicks", "impressions", "revenue"]:
            met_dict = res["models"][model_key]["metrics"][untracked_met]
            assert met_dict["points_evaluated"] == 0
            assert met_dict["mae"] is None
            assert met_dict["rmse"] is None
            assert met_dict["wape"] is None
            assert met_dict["wape_status"] == "no_evaluated_points"




