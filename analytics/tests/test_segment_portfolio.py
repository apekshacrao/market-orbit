import json
import numpy as np
import pandas as pd
import pytest

from analytics.segmentation.portfolio import profile_segment_portfolio
from analytics.segmentation.cohorts import classify_campaign_cohorts, profile_segment_portfolio as reexported_profile
from analytics.segmentation import profile_segment_portfolio as package_profile


def test_spend_and_conversion_share_exact():
    """1. Exact spend-share and conversion-share calculations."""
    df = pd.DataFrame([
        {"customer_segment": "Segment A", "spend": 300.0, "conversions": 30},
        {"customer_segment": "Segment B", "spend": 700.0, "conversions": 70},
    ])
    result = profile_segment_portfolio(df)

    assert result["is_available"] is True
    assert result["total_segments"] == 2
    segs = result["segments"]

    assert segs["Segment A"]["spend"] == 300.0
    assert segs["Segment A"]["conversions"] == 30
    assert segs["Segment A"]["share_of_spend"] == 30.0
    assert segs["Segment A"]["share_of_conversions"] == 30.0

    assert segs["Segment B"]["spend"] == 700.0
    assert segs["Segment B"]["conversions"] == 70
    assert segs["Segment B"]["share_of_spend"] == 70.0
    assert segs["Segment B"]["share_of_conversions"] == 70.0


def test_revenue_shares_with_complete_revenue():
    """2. Revenue shares with complete revenue data."""
    df = pd.DataFrame([
        {"customer_segment": "Enterprise", "spend": 500.0, "conversions": 50, "revenue": 1500.0},
        {"customer_segment": "SMB", "spend": 500.0, "conversions": 50, "revenue": 3500.0},
    ])
    result = profile_segment_portfolio(df)

    assert result["is_available"] is True
    segs = result["segments"]

    # Total revenue = 5000.0
    assert segs["Enterprise"]["revenue"] == 1500.0
    assert segs["Enterprise"]["share_of_revenue"] == 30.0
    assert segs["Enterprise"]["roas"] == 3.0

    assert segs["SMB"]["revenue"] == 3500.0
    assert segs["SMB"]["share_of_revenue"] == 70.0
    assert segs["SMB"]["roas"] == 7.0


def test_missing_and_partially_missing_revenue():
    """3. Missing and partially missing revenue handling."""
    # Case A: Revenue column completely absent
    df_no_rev = pd.DataFrame([
        {"customer_segment": "Seg A", "spend": 100.0, "conversions": 10},
        {"customer_segment": "Seg B", "spend": 200.0, "conversions": 20},
    ])
    res_no_rev = profile_segment_portfolio(df_no_rev)
    for seg in res_no_rev["segments"].values():
        assert seg["revenue"] is None
        assert seg["roas"] is None
        assert seg["share_of_revenue"] is None

    # Case B: Revenue column present but entirely null
    df_all_null = pd.DataFrame([
        {"customer_segment": "Seg A", "spend": 100.0, "conversions": 10, "revenue": None},
        {"customer_segment": "Seg B", "spend": 200.0, "conversions": 20, "revenue": np.nan},
    ])
    res_all_null = profile_segment_portfolio(df_all_null)
    for seg in res_all_null["segments"].values():
        assert seg["revenue"] is None
        assert seg["roas"] is None
        assert seg["share_of_revenue"] is None

    # Case C: Partially missing revenue across segments (Seg A complete, Seg B has NaN)
    df_partial = pd.DataFrame([
        {"customer_segment": "Seg A", "spend": 100.0, "conversions": 10, "revenue": 300.0},
        {"customer_segment": "Seg B", "spend": 200.0, "conversions": 20, "revenue": None},
    ])
    res_partial = profile_segment_portfolio(df_partial)
    # Seg A revenue was tracked in its own rows, but portfolio revenue is incomplete
    assert res_partial["segments"]["Seg A"]["revenue"] == 300.0
    assert res_partial["segments"]["Seg A"]["roas"] == 3.0
    assert res_partial["segments"]["Seg A"]["share_of_revenue"] is None

    # Seg B has missing revenue
    assert res_partial["segments"]["Seg B"]["revenue"] is None
    assert res_partial["segments"]["Seg B"]["roas"] is None
    assert res_partial["segments"]["Seg B"]["share_of_revenue"] is None


def test_explicit_zero_revenue_vs_untracked():
    """4. Explicit zero revenue versus untracked revenue."""
    df = pd.DataFrame([
        {"customer_segment": "ZeroRev", "spend": 100.0, "conversions": 10, "revenue": 0.0},
        {"customer_segment": "PosRev", "spend": 100.0, "conversions": 10, "revenue": 400.0},
    ])
    result = profile_segment_portfolio(df)

    segs = result["segments"]
    assert segs["ZeroRev"]["revenue"] == 0.0
    assert segs["ZeroRev"]["share_of_revenue"] == 0.0
    assert segs["ZeroRev"]["roas"] == 0.0

    assert segs["PosRev"]["revenue"] == 400.0
    assert segs["PosRev"]["share_of_revenue"] == 100.0
    assert segs["PosRev"]["roas"] == 4.0

    # Total portfolio revenue is explicitly zero
    df_all_zero = pd.DataFrame([
        {"customer_segment": "ZeroA", "spend": 100.0, "conversions": 10, "revenue": 0.0},
        {"customer_segment": "ZeroB", "spend": 100.0, "conversions": 10, "revenue": 0.0},
    ])
    res_all_zero = profile_segment_portfolio(df_all_zero)
    # If total portfolio revenue is zero, share_of_revenue must be None to avoid 0/0 division
    for s in res_all_zero["segments"].values():
        assert s["revenue"] == 0.0
        assert s["roas"] == 0.0
        assert s["share_of_revenue"] is None


def test_conversion_efficiency_ratios_above_below_equal_one():
    """5. Conversion-efficiency ratios above, below, and equal to 1."""
    # Total spend: 1000, Total conversions: 100
    df = pd.DataFrame([
        {"customer_segment": "OverIndexed", "spend": 200.0, "conversions": 40},   # spend 20%, conv 40% -> 2.0
        {"customer_segment": "UnderIndexed", "spend": 500.0, "conversions": 30},  # spend 50%, conv 30% -> 0.6
        {"customer_segment": "ParIndexed", "spend": 300.0, "conversions": 30},    # spend 30%, conv 30% -> 1.0
    ])
    result = profile_segment_portfolio(df)
    segs = result["segments"]

    assert segs["OverIndexed"]["share_of_spend"] == 20.0
    assert segs["OverIndexed"]["share_of_conversions"] == 40.0
    assert segs["OverIndexed"]["conversion_efficiency_ratio"] == 2.0
    assert segs["OverIndexed"]["conversion_efficiency_ratio"] > 1.0

    assert segs["UnderIndexed"]["share_of_spend"] == 50.0
    assert segs["UnderIndexed"]["share_of_conversions"] == 30.0
    assert segs["UnderIndexed"]["conversion_efficiency_ratio"] == 0.6
    assert segs["UnderIndexed"]["conversion_efficiency_ratio"] < 1.0

    assert segs["ParIndexed"]["share_of_spend"] == 30.0
    assert segs["ParIndexed"]["share_of_conversions"] == 30.0
    assert segs["ParIndexed"]["conversion_efficiency_ratio"] == 1.0


def test_cpa_index_below_above_equal_one_hundred():
    """6. CPA index below, above, and equal to 100."""
    # Total spend: 1000.0, Total conversions: 100 -> Portfolio CPA = 10.0
    df = pd.DataFrame([
        {"customer_segment": "CheapCPA", "spend": 200.0, "conversions": 40},     # CPA = 5.0 -> CPA index = 50.0
        {"customer_segment": "ExpensiveCPA", "spend": 400.0, "conversions": 20}, # CPA = 20.0 -> CPA index = 200.0
        {"customer_segment": "ParCPA", "spend": 400.0, "conversions": 40},       # CPA = 10.0 -> CPA index = 100.0
    ])
    result = profile_segment_portfolio(df)
    segs = result["segments"]

    assert segs["CheapCPA"]["cpa"] == 5.0
    assert segs["CheapCPA"]["cpa_index"] == 50.0
    assert segs["CheapCPA"]["cpa_index"] < 100.0

    assert segs["ExpensiveCPA"]["cpa"] == 20.0
    assert segs["ExpensiveCPA"]["cpa_index"] == 200.0
    assert segs["ExpensiveCPA"]["cpa_index"] > 100.0

    assert segs["ParCPA"]["cpa"] == 10.0
    assert segs["ParCPA"]["cpa_index"] == 100.0


def test_zero_total_spend():
    """7. Zero total spend handling."""
    df = pd.DataFrame([
        {"customer_segment": "Seg A", "spend": 0.0, "conversions": 10},
        {"customer_segment": "Seg B", "spend": 0.0, "conversions": 20},
    ])
    result = profile_segment_portfolio(df)

    assert result["is_available"] is True
    for seg in result["segments"].values():
        assert seg["spend"] == 0.0
        assert seg["share_of_spend"] is None
        assert seg["conversion_efficiency_ratio"] is None
        assert seg["cpa"] == 0.0
        assert seg["cpa_index"] is None  # portfolio CPA is 0.0, undefined index


def test_zero_total_conversions():
    """8. Zero total conversions handling."""
    df = pd.DataFrame([
        {"customer_segment": "Seg A", "spend": 100.0, "conversions": 0},
        {"customer_segment": "Seg B", "spend": 200.0, "conversions": 0},
    ])
    result = profile_segment_portfolio(df)

    assert result["is_available"] is True
    segs = result["segments"]

    assert segs["Seg A"]["share_of_spend"] == 33.33
    assert segs["Seg A"]["share_of_conversions"] is None
    assert segs["Seg A"]["conversion_efficiency_ratio"] is None
    assert segs["Seg A"]["cpa"] is None
    assert segs["Seg A"]["cpa_index"] is None

    assert segs["Seg B"]["share_of_spend"] == 66.67
    assert segs["Seg B"]["share_of_conversions"] is None
    assert segs["Seg B"]["conversion_efficiency_ratio"] is None
    assert segs["Seg B"]["cpa"] is None
    assert segs["Seg B"]["cpa_index"] is None


def test_zero_or_undefined_portfolio_cpa():
    """9. Zero or undefined portfolio CPA."""
    # Undefined portfolio CPA (zero conversions)
    df_no_conv = pd.DataFrame([
        {"customer_segment": "Seg A", "spend": 100.0, "conversions": 0},
    ])
    res_no_conv = profile_segment_portfolio(df_no_conv)
    assert res_no_conv["segments"]["Seg A"]["cpa_index"] is None

    # Zero portfolio CPA (zero spend with positive conversions)
    df_zero_cpa = pd.DataFrame([
        {"customer_segment": "FreeSeg", "spend": 0.0, "conversions": 10},
    ])
    res_zero_cpa = profile_segment_portfolio(df_zero_cpa)
    assert res_zero_cpa["segments"]["FreeSeg"]["cpa_index"] is None

    # Segment CPA undefined while portfolio CPA is positive
    df_mixed = pd.DataFrame([
        {"customer_segment": "Seg With Conv", "spend": 100.0, "conversions": 10},
        {"customer_segment": "Seg No Conv", "spend": 50.0, "conversions": 0},
    ])
    res_mixed = profile_segment_portfolio(df_mixed)
    assert res_mixed["segments"]["Seg With Conv"]["cpa_index"] is not None
    assert res_mixed["segments"]["Seg No Conv"]["cpa"] is None
    assert res_mixed["segments"]["Seg No Conv"]["cpa_index"] is None


def test_missing_customer_segment_column():
    """10. Missing customer_segment column."""
    df = pd.DataFrame([
        {"campaign_name": "Camp A", "spend": 100.0, "conversions": 10},
        {"campaign_name": "Camp B", "spend": 200.0, "conversions": 20},
    ])
    result = profile_segment_portfolio(df)

    assert result["is_available"] is False
    assert result["total_segments"] == 0
    assert result["segments"] == {}


def test_null_blank_sentinel_segment_labels():
    """11. Null, blank, and sentinel segment labels."""
    df = pd.DataFrame([
        {"customer_segment": None, "spend": 100.0, "conversions": 10},
        {"customer_segment": np.nan, "spend": 100.0, "conversions": 10},
        {"customer_segment": "", "spend": 100.0, "conversions": 10},
        {"customer_segment": "   ", "spend": 100.0, "conversions": 10},
        {"customer_segment": "nan", "spend": 100.0, "conversions": 10},
        {"customer_segment": "None", "spend": 100.0, "conversions": 10},
        {"customer_segment": "NAT", "spend": 100.0, "conversions": 10},
        {"customer_segment": "null", "spend": 100.0, "conversions": 10},
    ])
    result = profile_segment_portfolio(df)

    assert result["is_available"] is False
    assert result["total_segments"] == 0
    assert result["segments"] == {}


def test_partial_segment_label_coverage_and_denominator_consistency():
    """12. Partial segment-label coverage and denominator consistency."""
    df = pd.DataFrame([
        {"customer_segment": "Enterprise", "spend": 50.0, "conversions": 5, "revenue": 100.0},
        {"customer_segment": "SMB", "spend": 30.0, "conversions": 3, "revenue": 60.0},
        {"customer_segment": None, "spend": 20.0, "conversions": 2, "revenue": 40.0},
    ])
    result = profile_segment_portfolio(df)

    assert result["is_available"] is True
    assert result["total_segments"] == 2
    segs = result["segments"]

    assert "Enterprise" in segs
    assert "SMB" in segs
    assert None not in segs

    # Portfolio totals are calculated across the full dataset:
    # Total spend = 100.0, Total conversions = 10, Total revenue = 200.0
    assert segs["Enterprise"]["share_of_spend"] == 50.0
    assert segs["Enterprise"]["share_of_conversions"] == 50.0
    assert segs["Enterprise"]["share_of_revenue"] == 50.0

    assert segs["SMB"]["share_of_spend"] == 30.0
    assert segs["SMB"]["share_of_conversions"] == 30.0
    assert segs["SMB"]["share_of_revenue"] == 30.0

    # The sum of shares across labeled segments reflects partial coverage (80% spend, 80% conv, 80% rev)
    assert segs["Enterprise"]["share_of_spend"] + segs["SMB"]["share_of_spend"] == 80.0


def test_empty_input_and_single_segment_input():
    """13. Empty input and single-segment input."""
    # None input
    res_none = profile_segment_portfolio(None)
    assert res_none["is_available"] is False
    assert res_none["total_segments"] == 0
    assert res_none["segments"] == {}

    # Empty DataFrame
    res_empty = profile_segment_portfolio(pd.DataFrame())
    assert res_empty["is_available"] is False
    assert res_empty["total_segments"] == 0
    assert res_empty["segments"] == {}

    # Single segment
    df_single = pd.DataFrame([
        {"customer_segment": "OnlySegment", "spend": 100.0, "conversions": 10, "revenue": 200.0},
    ])
    res_single = profile_segment_portfolio(df_single)
    assert res_single["is_available"] is True
    assert res_single["total_segments"] == 1
    solo = res_single["segments"]["OnlySegment"]
    assert solo["spend"] == 100.0
    assert solo["conversions"] == 10
    assert solo["revenue"] == 200.0
    assert solo["share_of_spend"] == 100.0
    assert solo["share_of_conversions"] == 100.0
    assert solo["share_of_revenue"] == 100.0
    assert solo["conversion_efficiency_ratio"] == 1.0
    assert solo["cpa_index"] == 100.0


def test_deterministic_ordering_and_repeated_call_consistency():
    """14. Deterministic ordering and repeated-call consistency."""
    # Segments provided in reverse alphabetical order
    df = pd.DataFrame([
        {"customer_segment": "Zeta", "spend": 100.0, "conversions": 10},
        {"customer_segment": "Beta", "spend": 200.0, "conversions": 20},
        {"customer_segment": "Alpha", "spend": 300.0, "conversions": 30},
    ])

    res1 = profile_segment_portfolio(df)
    res2 = profile_segment_portfolio(df)

    assert list(res1["segments"].keys()) == ["Alpha", "Beta", "Zeta"]
    assert list(res2["segments"].keys()) == ["Alpha", "Beta", "Zeta"]
    assert res1 == res2


def test_strict_json_serialization_allow_nan_false():
    """15. Strict JSON serialization with allow_nan=False."""
    # Edge case with zero spend, missing revenue, partial sentinels
    df = pd.DataFrame([
        {"customer_segment": "Seg Zero", "spend": 0.0, "conversions": 0, "revenue": None},
        {"customer_segment": "Seg NonZero", "spend": 100.0, "conversions": 5, "revenue": 200.0},
        {"customer_segment": "nan", "spend": 50.0, "conversions": 2, "revenue": 100.0},
    ])

    result = profile_segment_portfolio(df)
    serialized = json.dumps(result, allow_nan=False)
    deserialized = json.loads(serialized)

    assert deserialized["is_available"] is True
    assert deserialized["total_segments"] == 2
    assert "Seg Zero" in deserialized["segments"]
    assert "Seg NonZero" in deserialized["segments"]


def test_regression_existing_cohort_entrypoint():
    """16. Regression test confirming existing cohort entrypoint remains unchanged."""
    data = [
        {"campaign_name": "Camp 1", "spend": 100.0, "conversions": 10, "customer_segment": "Seg A"},
        {"campaign_name": "Camp 2", "spend": 200.0, "conversions": 20, "customer_segment": "Seg B"},
    ]
    df = pd.DataFrame(data)

    cohort_result = classify_campaign_cohorts(df)
    assert cohort_result["summary"]["total_campaigns"] == 2
    assert len(cohort_result["cohorts"]["scale_ready"]) + \
           len(cohort_result["cohorts"]["volume_driver"]) + \
           len(cohort_result["cohorts"]["efficiency_niche"]) + \
           len(cohort_result["cohorts"]["budget_drain"]) == 2

    # Check that profile_segment_portfolio is callable from all exported paths
    res_direct = profile_segment_portfolio(df)
    res_reexport = reexported_profile(df)
    res_pkg = package_profile(df)
    assert res_direct == res_reexport == res_pkg
