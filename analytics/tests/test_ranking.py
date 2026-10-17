import numpy as np
import pandas as pd
import pytest

from analytics.performance.ranking import aggregate_campaigns, rank_campaigns


def test_correct_campaign_aggregation():
    """1. Correct campaign aggregation across multiple rows with derived metrics."""
    data = [
        {
            "campaign_name": "Campaign Alpha",
            "spend": 100.0,
            "conversions": 5,
            "clicks": 50,
            "impressions": 1000,
            "revenue": 300.0,
        },
        {
            "campaign_name": "Campaign Alpha",
            "spend": 200.0,
            "conversions": 15,
            "clicks": 150,
            "impressions": 3000,
            "revenue": 600.0,
        },
        {
            "campaign_name": "Campaign Beta",
            "spend": 50.0,
            "conversions": 2,
            "clicks": 25,
            "impressions": 500,
            "revenue": 100.0,
        },
    ]
    df = pd.DataFrame(data)
    results = aggregate_campaigns(df)

    assert len(results) == 2
    alpha = next(c for c in results if c["campaign_name"] == "Campaign Alpha")
    assert alpha["spend"] == 300.0
    assert alpha["conversions"] == 20
    assert alpha["clicks"] == 200
    assert alpha["impressions"] == 4000
    assert alpha["revenue"] == 900.0
    assert alpha["cpa"] == 15.0  # 300 / 20
    assert alpha["cpc"] == 1.5   # 300 / 200
    assert alpha["ctr"] == 5.0   # (200 / 4000) * 100
    assert alpha["conversion_rate"] == 10.0  # (20 / 200) * 100
    assert alpha["roas"] == 3.0  # 900 / 300
    assert alpha["roi"] == 200.0 # ((900 - 300) / 300) * 100


def test_roas_ranking_and_exclusion_of_unavailable_roas():
    """2. Correct ROAS ranking and exclusion of unavailable ROAS."""
    data = [
        {"campaign_name": "High ROAS", "spend": 100.0, "conversions": 10, "revenue": 400.0},
        {"campaign_name": "Mid ROAS", "spend": 100.0, "conversions": 10, "revenue": 200.0},
        {"campaign_name": "No Revenue", "spend": 100.0, "conversions": 10, "revenue": None},
        {"campaign_name": "Zero Spend", "spend": 0.0, "conversions": 10, "revenue": 100.0},
    ]
    df = pd.DataFrame(data)
    rankings = rank_campaigns(df, top_n=2)

    roas_top = rankings["by_roas"]["top"]
    assert len(roas_top) == 2
    assert roas_top[0]["campaign_name"] == "High ROAS"
    assert roas_top[0]["roas"] == 4.0
    assert roas_top[1]["campaign_name"] == "Mid ROAS"
    assert roas_top[1]["roas"] == 2.0

    # Ensure campaigns with unavailable ROAS are excluded
    all_roas_names = {c["campaign_name"] for c in rankings["by_roas"]["top"] + rankings["by_roas"]["bottom"]}
    assert "No Revenue" not in all_roas_names
    assert "Zero Spend" not in all_roas_names

    assert rankings["summary"]["total_campaigns_evaluated"] == 4
    assert rankings["summary"]["campaigns_with_roas"] == 2


def test_cpa_ranking_and_exclusion_of_undefined_cpa():
    """3. Correct CPA ranking (lower is better) and exclusion of undefined CPA."""
    data = [
        {"campaign_name": "Best CPA", "spend": 100.0, "conversions": 20, "revenue": 200.0},
        {"campaign_name": "Worst CPA", "spend": 200.0, "conversions": 5, "revenue": 200.0},
        {"campaign_name": "Zero Conversions", "spend": 100.0, "conversions": 0, "revenue": 200.0},
    ]
    df = pd.DataFrame(data)
    rankings = rank_campaigns(df, top_n=2)

    cpa_top = rankings["by_cpa"]["top"]
    assert len(cpa_top) == 2
    # Best CPA is lowest CPA (100 / 20 = 5.0)
    assert cpa_top[0]["campaign_name"] == "Best CPA"
    assert cpa_top[0]["cpa"] == 5.0
    # Next is 200 / 5 = 40.0
    assert cpa_top[1]["campaign_name"] == "Worst CPA"
    assert cpa_top[1]["cpa"] == 40.0

    # Undefined CPA (0 conversions) must be excluded from CPA rankings
    all_cpa_names = {c["campaign_name"] for c in rankings["by_cpa"]["top"] + rankings["by_cpa"]["bottom"]}
    assert "Zero Conversions" not in all_cpa_names
    assert rankings["summary"]["campaigns_with_cpa"] == 2


def test_conversion_volume_ranking():
    """4. Correct conversion-volume ranking (higher is better)."""
    data = [
        {"campaign_name": "Low Conv", "spend": 100.0, "conversions": 5},
        {"campaign_name": "High Conv", "spend": 100.0, "conversions": 100},
        {"campaign_name": "Mid Conv", "spend": 100.0, "conversions": 45},
    ]
    df = pd.DataFrame(data)
    rankings = rank_campaigns(df, top_n=3)

    conv_top = rankings["by_conversions"]["top"]
    assert len(conv_top) == 3
    assert conv_top[0]["campaign_name"] == "High Conv"
    assert conv_top[0]["conversions"] == 100
    assert conv_top[1]["campaign_name"] == "Mid Conv"
    assert conv_top[1]["conversions"] == 45
    assert conv_top[2]["campaign_name"] == "Low Conv"
    assert conv_top[2]["conversions"] == 5


def test_zero_conversions_and_zero_clicks():
    """5. Zero conversions and zero clicks do not divide by zero and return None."""
    data = [
        {
            "campaign_name": "No Clicks No Conv",
            "spend": 150.0,
            "conversions": 0,
            "clicks": 0,
            "impressions": 500,
            "revenue": None,
        }
    ]
    df = pd.DataFrame(data)
    results = aggregate_campaigns(df)

    item = results[0]
    assert item["cpa"] is None
    assert item["cpc"] is None
    assert item["conversion_rate"] is None
    assert item["ctr"] == 0.0  # 0 / 500 * 100 = 0.0


def test_zero_spend():
    """6. Zero spend produces None for ROAS and ROI without producing infinity or NaN."""
    data = [
        {
            "campaign_name": "Zero Spend",
            "spend": 0.0,
            "conversions": 10,
            "clicks": 50,
            "impressions": 1000,
            "revenue": 300.0,
        }
    ]
    df = pd.DataFrame(data)
    results = aggregate_campaigns(df)

    item = results[0]
    assert item["spend"] == 0.0
    assert item["roas"] is None
    assert item["roi"] is None
    assert item["cpa"] == 0.0
    assert item["cpc"] == 0.0


def test_missing_revenue_versus_explicitly_zero_revenue():
    """7. Missing revenue vs explicitly zero revenue remains distinguishable."""
    data = [
        {"campaign_name": "Untracked Rev", "spend": 100.0, "conversions": 5, "revenue": None},
        {"campaign_name": "Explicit Zero Rev", "spend": 100.0, "conversions": 5, "revenue": 0.0},
    ]
    df = pd.DataFrame(data)
    results = aggregate_campaigns(df)

    untracked = next(c for c in results if c["campaign_name"] == "Untracked Rev")
    assert untracked["revenue"] is None
    assert untracked["roas"] is None
    assert untracked["roi"] is None

    explicit_zero = next(c for c in results if c["campaign_name"] == "Explicit Zero Rev")
    assert explicit_zero["revenue"] == 0.0
    assert explicit_zero["roas"] == 0.0
    assert explicit_zero["roi"] == -100.0

    rankings = rank_campaigns(df, top_n=5)
    # Explicit zero revenue is a valid ROAS of 0.0 and should be present in ROAS ranking
    roas_names = [c["campaign_name"] for c in rankings["by_roas"]["top"]]
    assert "Explicit Zero Rev" in roas_names
    assert "Untracked Rev" not in roas_names


def test_all_null_revenue_aggregation():
    """8. All-null revenue aggregation preserves None and does not convert to 0.0."""
    data = [
        {"campaign_name": "Campaign All Null", "spend": 50.0, "conversions": 2, "revenue": None},
        {"campaign_name": "Campaign All Null", "spend": 70.0, "conversions": 3, "revenue": np.nan},
    ]
    df = pd.DataFrame(data)
    results = aggregate_campaigns(df)

    assert len(results) == 1
    item = results[0]
    assert item["revenue"] is None
    assert item["roas"] is None
    assert item["roi"] is None

    rankings = rank_campaigns(df, top_n=5)
    assert rankings["by_roas"]["top"] == []
    assert rankings["by_roas"]["bottom"] == []
    assert rankings["summary"]["campaigns_with_roas"] == 0


def test_partially_missing_revenue_aggregation():
    """9. Partially missing revenue within a campaign is treated as incomplete (None)."""
    data = [
        {"campaign_name": "Partial Rev", "spend": 100.0, "conversions": 5, "revenue": 500.0},
        {"campaign_name": "Partial Rev", "spend": 100.0, "conversions": 5, "revenue": None},
    ]
    df = pd.DataFrame(data)
    results = aggregate_campaigns(df)

    item = results[0]
    # Incomplete revenue cannot be silently assumed complete
    assert item["revenue"] is None
    assert item["roas"] is None
    assert item["roi"] is None


def test_deterministic_ordering_on_metric_ties():
    """10. Deterministic tie-breaking uses campaign name for stable ordering."""
    data = [
        {"campaign_name": "Campaign Charlie", "spend": 100.0, "conversions": 10, "revenue": 200.0},
        {"campaign_name": "Campaign Alpha", "spend": 100.0, "conversions": 10, "revenue": 200.0},
        {"campaign_name": "Campaign Bravo", "spend": 100.0, "conversions": 10, "revenue": 200.0},
    ]
    df = pd.DataFrame(data)

    rankings1 = rank_campaigns(df, top_n=3)
    # Shuffled input order
    rankings2 = rank_campaigns(df.iloc[::-1], top_n=3)

    order1 = [c["campaign_name"] for c in rankings1["by_roas"]["top"]]
    order2 = [c["campaign_name"] for c in rankings2["by_roas"]["top"]]

    assert order1 == ["Campaign Alpha", "Campaign Bravo", "Campaign Charlie"]
    assert order1 == order2

    cpa_order = [c["campaign_name"] for c in rankings1["by_cpa"]["top"]]
    assert cpa_order == ["Campaign Alpha", "Campaign Bravo", "Campaign Charlie"]

    conv_order = [c["campaign_name"] for c in rankings1["by_conversions"]["top"]]
    assert conv_order == ["Campaign Alpha", "Campaign Bravo", "Campaign Charlie"]


def test_empty_input_and_missing_optional_columns():
    """11. Handles empty inputs and missing optional columns gracefully."""
    # Empty DataFrame
    empty_res = rank_campaigns(pd.DataFrame())
    assert empty_res["top"] == []
    assert empty_res["bottom"] == []
    assert empty_res["by_roas"]["top"] == []
    assert empty_res["by_cpa"]["top"] == []
    assert empty_res["by_conversions"]["top"] == []
    assert empty_res["summary"]["total_campaigns_evaluated"] == 0

    # Missing campaign_name column
    no_name_res = rank_campaigns(pd.DataFrame({"spend": [100.0]}))
    assert no_name_res["top"] == []

    # Missing optional revenue, impressions, clicks columns
    minimal_df = pd.DataFrame([
        {"campaign_name": "Camp A", "spend": 100.0, "conversions": 5},
    ])
    res = rank_campaigns(minimal_df)
    assert res["summary"]["total_campaigns_evaluated"] == 1
    camp = res["by_conversions"]["top"][0]
    assert camp["revenue"] is None
    assert camp["impressions"] == 0
    assert camp["clicks"] == 0
    assert camp["cpa"] == 20.0
    assert camp["ctr"] is None
    assert camp["cpc"] is None

    # top_n <= 0
    zero_n = rank_campaigns(minimal_df, top_n=0)
    assert zero_n["top"] == []


def test_backward_compatibility_top_and_bottom():
    """12. Backward compatibility of top and bottom outputs with existing callers."""
    # When ROAS is available
    data_with_roas = [
        {"campaign_name": "Camp A", "spend": 100.0, "conversions": 10, "revenue": 300.0},
        {"campaign_name": "Camp B", "spend": 100.0, "conversions": 5, "revenue": 150.0},
    ]
    rankings = rank_campaigns(pd.DataFrame(data_with_roas))
    assert "top" in rankings
    assert "bottom" in rankings
    assert len(rankings["top"]) == 2
    assert rankings["top"][0]["campaign_name"] == "Camp A"
    assert rankings["top"][0]["roas"] == 3.0

    # When revenue is untracked across all campaigns (fallback ranking preserves caller contract)
    data_no_roas = [
        {"campaign_name": "Camp X", "spend": 500.0, "conversions": 10, "revenue": None},
    ]
    rankings_fallback = rank_campaigns(pd.DataFrame(data_no_roas))
    assert len(rankings_fallback["top"]) == 1
    assert len(rankings_fallback["bottom"]) == 1
    assert rankings_fallback["top"][0]["campaign_name"] == "Camp X"
    assert rankings_fallback["top"][0]["revenue"] is None
    assert rankings_fallback["top"][0]["roas"] is None
    assert rankings_fallback["bottom"][0]["campaign_name"] == "Camp X"

