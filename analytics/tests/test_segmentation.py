import json
import numpy as np
import pandas as pd
import pytest

from analytics.segmentation.cohorts import classify_campaign_cohorts


def test_classification_all_four_cohorts():
    """1. Correct classification into all four cohorts based on median conversion and portfolio CPA."""
    # Total spend: 1000.0, Total conversions: 100 -> Portfolio CPA = 10.0
    # Conversions: [10, 20, 30, 40] -> Median conversions = (20 + 30) / 2 = 25.0
    data = [
        {"campaign_name": "Scale Ready Camp", "spend": 200.0, "conversions": 40, "revenue": 600.0},     # conv 40 >= 25, CPA 5.0 <= 10.0 -> scale_ready
        {"campaign_name": "Volume Driver Camp", "spend": 450.0, "conversions": 30, "revenue": 900.0},   # conv 30 >= 25, CPA 15.0 > 10.0 -> volume_driver
        {"campaign_name": "Efficiency Niche Camp", "spend": 160.0, "conversions": 20, "revenue": 300.0},# conv 20 < 25, CPA 8.0 <= 10.0 -> efficiency_niche
        {"campaign_name": "Budget Drain Camp", "spend": 190.0, "conversions": 10, "revenue": 100.0},    # conv 10 < 25, CPA 19.0 > 10.0 -> budget_drain
    ]
    df = pd.DataFrame(data)
    result = classify_campaign_cohorts(df)

    summary = result["summary"]
    assert summary["total_campaigns"] == 4
    assert summary["scale_ready_count"] == 1
    assert summary["volume_driver_count"] == 1
    assert summary["efficiency_niche_count"] == 1
    assert summary["budget_drain_count"] == 1

    cohorts = result["cohorts"]
    assert cohorts["scale_ready"][0]["campaign_name"] == "Scale Ready Camp"
    assert cohorts["scale_ready"][0]["cpa"] == 5.0
    assert cohorts["scale_ready"][0]["roas"] == 3.0

    assert cohorts["volume_driver"][0]["campaign_name"] == "Volume Driver Camp"
    assert cohorts["volume_driver"][0]["cpa"] == 15.0

    assert cohorts["efficiency_niche"][0]["campaign_name"] == "Efficiency Niche Camp"
    assert cohorts["efficiency_niche"][0]["cpa"] == 8.0

    assert cohorts["budget_drain"][0]["campaign_name"] == "Budget Drain Camp"
    assert cohorts["budget_drain"][0]["cpa"] == 19.0


def test_median_calculation_odd_and_even_counts():
    """2. Median conversion count calculation behaves correctly for odd and even counts."""
    # Odd count (3 campaigns): conversions = [5, 15, 25] -> median = 15.0
    odd_data = [
        {"campaign_name": "Low", "spend": 50.0, "conversions": 5},
        {"campaign_name": "Mid", "spend": 150.0, "conversions": 15},
        {"campaign_name": "High", "spend": 250.0, "conversions": 25},
    ]
    odd_res = classify_campaign_cohorts(pd.DataFrame(odd_data))
    # Mid has conversions == 15.0 (>= median 15.0) -> high volume
    # Portfolio CPA = (50+150+250) / (5+15+25) = 450 / 45 = 10.0
    # Mid CPA = 150 / 15 = 10.0 (<= portfolio CPA 10.0) -> scale_ready
    assert odd_res["summary"]["total_campaigns"] == 3
    assert any(c["campaign_name"] == "Mid" for c in odd_res["cohorts"]["scale_ready"])

    # Even count (4 campaigns): conversions = [10, 20, 30, 40] -> median = 25.0
    even_data = [
        {"campaign_name": "C1", "spend": 100.0, "conversions": 10},
        {"campaign_name": "C2", "spend": 100.0, "conversions": 20},
        {"campaign_name": "C3", "spend": 100.0, "conversions": 30},
        {"campaign_name": "C4", "spend": 100.0, "conversions": 40},
    ]
    even_res = classify_campaign_cohorts(pd.DataFrame(even_data))
    # C2 has conversions 20 < 25.0 -> low volume
    # C3 has conversions 30 >= 25.0 -> high volume
    assert any(c["campaign_name"] == "C3" for c in even_res["cohorts"]["scale_ready"] + even_res["cohorts"]["volume_driver"])
    assert any(c["campaign_name"] == "C2" for c in even_res["cohorts"]["efficiency_niche"] + even_res["cohorts"]["budget_drain"])


def test_conversion_count_ties_at_median():
    """3. Campaigns with conversion counts tied exactly at the median are classified as high volume."""
    # Conversions: [20, 20, 20] -> median = 20.0
    # Total spend = 600.0, Total conv = 60 -> Portfolio CPA = 10.0
    data = [
        {"campaign_name": "Tied Low CPA", "spend": 160.0, "conversions": 20},   # CPA 8.0 <= 10.0 -> scale_ready
        {"campaign_name": "Tied Mid CPA", "spend": 200.0, "conversions": 20},   # CPA 10.0 <= 10.0 -> scale_ready
        {"campaign_name": "Tied High CPA", "spend": 240.0, "conversions": 20},  # CPA 12.0 > 10.0 -> volume_driver
    ]
    df = pd.DataFrame(data)
    result = classify_campaign_cohorts(df)

    assert result["summary"]["scale_ready_count"] == 2
    assert result["summary"]["volume_driver_count"] == 1
    assert result["summary"]["efficiency_niche_count"] == 0
    assert result["summary"]["budget_drain_count"] == 0


def test_positive_spend_zero_conversions_always_budget_drain():
    """4. Positive spend campaigns with zero conversions always enter budget_drain."""
    data = [
        {"campaign_name": "Good Campaign", "spend": 200.0, "conversions": 20},
        {"campaign_name": "Wasted Campaign 1", "spend": 500.0, "conversions": 0},
        {"campaign_name": "Wasted Campaign 2", "spend": 250.0, "conversions": 0},
    ]
    df = pd.DataFrame(data)
    result = classify_campaign_cohorts(df)

    drain = result["cohorts"]["budget_drain"]
    assert len(drain) == 2
    # Wasted campaigns must be in budget drain and sorted by spend descending
    assert drain[0]["campaign_name"] == "Wasted Campaign 1"
    assert drain[0]["spend"] == 500.0
    assert drain[0]["conversions"] == 0
    assert drain[0]["cpa"] is None

    assert drain[1]["campaign_name"] == "Wasted Campaign 2"
    assert drain[1]["spend"] == 250.0


def test_zero_portfolio_conversions_and_undefined_cpa():
    """5. Datasets where total conversions is zero route all campaigns safely to budget_drain."""
    data = [
        {"campaign_name": "Zero A", "spend": 100.0, "conversions": 0},
        {"campaign_name": "Zero B", "spend": 200.0, "conversions": 0},
    ]
    df = pd.DataFrame(data)
    result = classify_campaign_cohorts(df)

    summary = result["summary"]
    assert summary["total_campaigns"] == 2
    assert summary["scale_ready_count"] == 0
    assert summary["volume_driver_count"] == 0
    assert summary["efficiency_niche_count"] == 0
    assert summary["budget_drain_count"] == 2


def test_zero_spend_campaigns_and_single_campaign_dataset():
    """6. Single-campaign datasets and zero-spend campaigns are handled deterministically."""
    # Single campaign with conversions > 0
    single_valid = pd.DataFrame([
        {"campaign_name": "Solo Active", "spend": 100.0, "conversions": 10}
    ])
    res_solo = classify_campaign_cohorts(single_valid)
    assert res_solo["summary"]["total_campaigns"] == 1
    assert res_solo["summary"]["scale_ready_count"] == 1
    assert res_solo["cohorts"]["scale_ready"][0]["campaign_name"] == "Solo Active"

    # Single campaign with 0 spend and 0 conversions
    single_zero = pd.DataFrame([
        {"campaign_name": "Solo Inactive", "spend": 0.0, "conversions": 0}
    ])
    res_zero = classify_campaign_cohorts(single_zero)
    assert res_zero["summary"]["total_campaigns"] == 1
    assert res_zero["summary"]["budget_drain_count"] == 1

    # Zero spend with positive conversions (organic / free conversions)
    free_conv = pd.DataFrame([
        {"campaign_name": "Organic Viral", "spend": 0.0, "conversions": 50},
        {"campaign_name": "Paid Support", "spend": 100.0, "conversions": 10},
    ])
    res_free = classify_campaign_cohorts(free_conv)
    # Organic Viral has CPA = 0.0, which is <= portfolio CPA -> scale_ready
    assert any(c["campaign_name"] == "Organic Viral" for c in res_free["cohorts"]["scale_ready"])


def test_missing_and_null_revenue_no_fabricated_roas():
    """7. Preserves null revenue semantics and never invents ROAS."""
    data = [
        {"campaign_name": "Tracked Rev", "spend": 100.0, "conversions": 10, "revenue": 300.0},
        {"campaign_name": "Untracked Rev", "spend": 100.0, "conversions": 10, "revenue": None},
    ]
    df = pd.DataFrame(data)
    result = classify_campaign_cohorts(df)

    tracked = next(c for c in result["cohorts"]["scale_ready"] if c["campaign_name"] == "Tracked Rev")
    assert tracked["roas"] == 3.0

    untracked = next(c for c in result["cohorts"]["scale_ready"] if c["campaign_name"] == "Untracked Rev")
    assert untracked["roas"] is None


def test_empty_input_and_missing_required_columns():
    """8. Empty DataFrame, None input, and missing required columns return valid empty structure."""
    res_none = classify_campaign_cohorts(None)
    assert res_none["summary"]["total_campaigns"] == 0
    assert res_none["cohorts"]["scale_ready"] == []

    res_empty = classify_campaign_cohorts(pd.DataFrame())
    assert res_empty["summary"]["total_campaigns"] == 0

    res_missing_col = classify_campaign_cohorts(pd.DataFrame([{"spend": 100.0, "conversions": 5}]))
    assert res_missing_col["summary"]["total_campaigns"] == 0


def test_deterministic_ordering_and_repeated_calls():
    """9. Output is stable and identical across repeated executions and row shuffling."""
    data = [
        {"campaign_name": "Zeta", "spend": 100.0, "conversions": 10},
        {"campaign_name": "Alpha", "spend": 200.0, "conversions": 30},
        {"campaign_name": "Beta", "spend": 150.0, "conversions": 5},
        {"campaign_name": "Gamma", "spend": 300.0, "conversions": 25},
    ]
    df1 = pd.DataFrame(data)
    df2 = df1.sample(frac=1.0, random_state=42).reset_index(drop=True)

    res1 = classify_campaign_cohorts(df1)
    res2 = classify_campaign_cohorts(df2)

    assert res1 == res2


def test_exactly_one_cohort_assignment_per_campaign():
    """10. Every campaign is assigned to exactly one cohort (mutually exclusive and collectively exhaustive)."""
    data = [
        {"campaign_name": f"Camp {i}", "spend": float(i * 50), "conversions": i * 5}
        for i in range(15)
    ]
    df = pd.DataFrame(data)
    result = classify_campaign_cohorts(df)

    total = result["summary"]["total_campaigns"]
    assert total == 15

    cohort_names = ["scale_ready", "volume_driver", "efficiency_niche", "budget_drain"]
    assigned_campaigns = []
    cohort_sets = []

    for name in cohort_names:
        campaign_names_in_cohort = [c["campaign_name"] for c in result["cohorts"][name]]
        assigned_campaigns.extend(campaign_names_in_cohort)
        cohort_sets.append(set(campaign_names_in_cohort))

    # Total assigned equals total evaluated
    assert len(assigned_campaigns) == total

    # Check pairwise mutual exclusivity
    for i in range(len(cohort_sets)):
        for j in range(i + 1, len(cohort_sets)):
            assert cohort_sets[i].isdisjoint(cohort_sets[j])

    # Check summary count integrity
    assert sum(result["summary"][f"{c}_count"] for c in cohort_names) == total


def test_strict_json_serialization_allow_nan_false():
    """11. All cohort results serialize cleanly with json.dumps(..., allow_nan=False)."""
    data = [
        {"campaign_name": "Camp A", "spend": 0.0, "conversions": 0, "clicks": 0, "revenue": None},
        {"campaign_name": "Camp B", "spend": 100.0, "conversions": 5, "clicks": 50, "revenue": 0.0},
        {"campaign_name": "Camp C", "spend": 200.0, "conversions": 20, "clicks": 100, "revenue": 400.0},
    ]
    df = pd.DataFrame(data)
    result = classify_campaign_cohorts(df)

    json_str = json.dumps(result, allow_nan=False)
    assert isinstance(json_str, str)
    assert "NaN" not in json_str
    assert "Infinity" not in json_str

    parsed = json.loads(json_str)
    assert parsed["summary"]["total_campaigns"] == 3
