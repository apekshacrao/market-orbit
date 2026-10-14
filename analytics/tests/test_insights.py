import json
import numpy as np
import pandas as pd
import pytest

from analytics.insights.generator import generate_insights
from analytics.kpi.metrics import calculate_kpis
from analytics.performance.ranking import rank_campaigns
from analytics.trends.customer_trends import analyze_trends
from analytics.preprocessing.cleaner import clean_dataset


def test_campaign_performance_insights_valid_evidence():
    """1. Campaign performance insight identifies top conversion driver with verified evidence."""
    data = [
        {"campaign_name": "Summer Launch", "spend": 400.0, "conversions": 40, "clicks": 400, "impressions": 8000, "revenue": 1200.0},
        {"campaign_name": "Brand Search", "spend": 200.0, "conversions": 10, "clicks": 100, "impressions": 2000, "revenue": 300.0},
    ]
    df = pd.DataFrame(data)
    insights = generate_insights(df=df)

    perf_insights = [i for i in insights if i["type"] == "campaign_performance"]
    assert len(perf_insights) >= 1

    top_conv = next(i for i in perf_insights if "Top Conversion Driver" in i["title"])
    assert top_conv["metric"] == "conversions"
    assert "Summer Launch" in top_conv["title"]
    assert top_conv["evidence"]["campaign_name"] == "Summer Launch"
    assert top_conv["evidence"]["conversions"] == 40
    assert top_conv["evidence"]["spend"] == 400.0


def test_zero_conversion_waste_detection():
    """2. Cost waste detection identifies positive-spend zero-conversion campaigns."""
    data = [
        {"campaign_name": "Working Campaign", "spend": 200.0, "conversions": 10, "clicks": 100, "impressions": 2000},
        {"campaign_name": "Wasted Campaign", "spend": 150.0, "conversions": 0, "clicks": 50, "impressions": 1000},
    ]
    df = pd.DataFrame(data)
    insights = generate_insights(df=df)

    waste_insights = [i for i in insights if "Zero-Conversion Spend" in i["title"]]
    assert len(waste_insights) == 1
    w = waste_insights[0]
    assert w["metric"] == "spend"
    assert w["evidence"]["campaign_name"] == "Wasted Campaign"
    assert w["evidence"]["spend"] == 150.0
    assert w["evidence"]["conversions"] == 0


def test_cost_efficiency_lowest_and_highest_cpa():
    """3. Cost efficiency comparisons identify lowest and highest CPA campaigns when valid."""
    data = [
        {"campaign_name": "Efficient Ad", "spend": 100.0, "conversions": 20},  # CPA = 5.0
        {"campaign_name": "Moderate Ad", "spend": 200.0, "conversions": 20},   # CPA = 10.0
        {"campaign_name": "Expensive Ad", "spend": 500.0, "conversions": 20},  # CPA = 25.0
    ]
    df = pd.DataFrame(data)
    insights = generate_insights(df=df)

    cost_insights = [i for i in insights if i["type"] == "cost_efficiency"]
    assert len(cost_insights) == 2

    best = next(i for i in cost_insights if "Lowest Cost per Acquisition" in i["title"])
    assert best["evidence"]["campaign_name"] == "Efficient Ad"
    assert best["evidence"]["cpa"] == 5.0

    worst = next(i for i in cost_insights if "Highest Cost per Acquisition" in i["title"])
    assert worst["evidence"]["campaign_name"] == "Expensive Ad"
    assert worst["evidence"]["cpa"] == 25.0


def test_roas_revenue_efficiency_complete_revenue():
    """4. ROAS and revenue efficiency insights generated only when revenue is complete."""
    data = [
        {"campaign_name": "High ROAS Campaign", "spend": 200.0, "conversions": 10, "revenue": 800.0},  # ROAS = 4.0
        {"campaign_name": "Low ROAS Campaign", "spend": 300.0, "conversions": 10, "revenue": 300.0},   # ROAS = 1.0
    ]
    df = pd.DataFrame(data)
    insights = generate_insights(df=df)

    roas_insights = [i for i in insights if i["type"] == "revenue_efficiency"]
    assert len(roas_insights) == 2

    top = next(i for i in roas_insights if "Top Return on Ad Spend" in i["title"])
    assert top["evidence"]["campaign_name"] == "High ROAS Campaign"
    assert top["evidence"]["roas"] == 4.0

    bottom = next(i for i in roas_insights if "Lowest Return on Ad Spend" in i["title"])
    assert bottom["evidence"]["campaign_name"] == "Low ROAS Campaign"
    assert bottom["evidence"]["roas"] == 1.0


def test_untracked_and_partially_missing_revenue():
    """5. Missing or partially missing revenue suppresses ROAS/ROI claims and emits data quality insight."""
    # Untracked revenue case
    data_untracked = [
        {"campaign_name": "Camp A", "spend": 100.0, "conversions": 5, "revenue": None},
        {"campaign_name": "Camp B", "spend": 200.0, "conversions": 10, "revenue": None},
    ]
    df_untracked = pd.DataFrame(data_untracked)
    insights_untracked = generate_insights(df=df_untracked)

    # Must NOT emit revenue_efficiency insights
    assert not any(i["type"] == "revenue_efficiency" for i in insights_untracked)

    # Must emit data_quality insight for missing revenue
    dq_rev = [i for i in insights_untracked if i["type"] == "data_quality" and i["metric"] == "revenue"]
    assert len(dq_rev) == 1
    assert dq_rev[0]["title"] == "Revenue Tracking Incomplete"
    assert dq_rev[0]["evidence"]["total_revenue"] is None

    # Partially missing revenue case
    data_partial = [
        {"campaign_name": "Camp A", "spend": 100.0, "conversions": 5, "revenue": 300.0},
        {"campaign_name": "Camp B", "spend": 200.0, "conversions": 10, "revenue": np.nan},
    ]
    df_partial = pd.DataFrame(data_partial)
    insights_partial = generate_insights(df=df_partial)

    # Total revenue is incomplete, so data_quality insight must be emitted
    dq_part = [i for i in insights_partial if i["type"] == "data_quality" and i["metric"] == "revenue"]
    assert len(dq_part) == 1


def test_historical_time_series_observations_valid_dates():
    """6. Historical time-series comparisons describe observed dates without extrapolation."""
    data = [
        {"campaign_name": "Camp A", "date": "2026-09-01", "spend": 100.0, "conversions": 5},
        {"campaign_name": "Camp A", "date": "2026-09-05", "spend": 250.0, "conversions": 25},
        {"campaign_name": "Camp A", "date": "2026-09-10", "spend": 200.0, "conversions": 15},
    ]
    df = pd.DataFrame(data)
    insights = generate_insights(df=df)

    ts_insights = [i for i in insights if i["type"] == "time_series"]
    assert len(ts_insights) >= 1

    progression = next(i for i in ts_insights if "Timeline Progression" in i["title"])
    assert progression["evidence"]["start_date"] == "2026-09-01"
    assert progression["evidence"]["end_date"] == "2026-09-10"
    assert progression["evidence"]["observed_dates_count"] == 3

    peak = next(i for i in ts_insights if "Peak Conversion Date" in i["title"])
    assert peak["evidence"]["date"] == "2026-09-05"
    assert peak["evidence"]["conversions"] == 25


def test_insufficient_time_series_coverage():
    """7. Single-date datasets emit data_quality alert and suppress time_series trend claims."""
    data = [
        {"campaign_name": "Camp A", "date": "2026-09-01", "spend": 100.0, "conversions": 5},
        {"campaign_name": "Camp B", "date": "2026-09-01", "spend": 200.0, "conversions": 10},
    ]
    df = pd.DataFrame(data)
    insights = generate_insights(df=df)

    # No multi-day time_series claims
    assert not any(i["type"] == "time_series" for i in insights)

    # Data quality alert for dates
    dq_dates = [i for i in insights if i["type"] == "data_quality" and i["metric"] == "date"]
    assert len(dq_dates) == 1
    assert dq_dates[0]["evidence"]["distinct_dates_count"] == 1
    assert dq_dates[0]["evidence"]["required_minimum_dates"] == 2


def test_dimensional_insights_multiple_categories():
    """8. Dimensional comparisons identify leading volume and best cost efficiency across categories."""
    data = [
        {"campaign_name": "Camp 1", "location": "US", "device": "Mobile", "spend": 300.0, "conversions": 30}, # CPA 10.0
        {"campaign_name": "Camp 2", "location": "EU", "device": "Desktop", "spend": 200.0, "conversions": 10}, # CPA 20.0
    ]
    df = pd.DataFrame(data)
    insights = generate_insights(df=df)

    dim_insights = [i for i in insights if i["type"] == "dimensional"]
    assert len(dim_insights) >= 2

    # Check location dimension leading conversion category
    loc_lead = next(i for i in dim_insights if "Leading Location by Conversions" in i["title"])
    assert loc_lead["evidence"]["category"] == "US"
    assert loc_lead["evidence"]["conversions"] == 30

    # Check device dimension leading conversion category
    dev_lead = next(i for i in dim_insights if "Leading Device by Conversions" in i["title"])
    assert dev_lead["evidence"]["category"] == "Mobile"
    assert dev_lead["evidence"]["conversions"] == 30


def test_missing_and_single_category_dimensions():
    """9. Missing dimensions or dimensions with only 1 category emit no comparative dimensional insights."""
    data = [
        {"campaign_name": "Camp 1", "location": "US", "spend": 100.0, "conversions": 10},
        {"campaign_name": "Camp 2", "location": "US", "spend": 150.0, "conversions": 15},
    ]
    df = pd.DataFrame(data)
    insights = generate_insights(df=df)

    # Only 1 unique location ("US") and other dimensions omitted -> no dimensional comparisons
    dim_insights = [i for i in insights if i["type"] == "dimensional"]
    assert len(dim_insights) == 0


def test_empty_datasets_and_undefined_metrics():
    """10. Handles empty datasets and undefined metrics gracefully without error."""
    assert generate_insights(df=pd.DataFrame()) == []
    assert generate_insights(df=None) == []

    # Dataset with zero spend and zero conversions
    zero_df = pd.DataFrame([
        {"campaign_name": "Empty Camp", "spend": 0.0, "conversions": 0, "clicks": 0, "impressions": 0}
    ])
    zero_insights = generate_insights(df=zero_df)
    # Undefined metrics do not crash or output NaN
    assert isinstance(zero_insights, list)
    serialized = json.dumps(zero_insights, allow_nan=False)
    assert "NaN" not in serialized


def test_deterministic_ordering_and_output_stability():
    """11. Identical inputs and shuffled inputs produce deterministic insight output and sequential IDs."""
    data = [
        {"campaign_name": "Zeta", "spend": 100.0, "conversions": 10, "revenue": 300.0, "location": "US"},
        {"campaign_name": "Alpha", "spend": 200.0, "conversions": 30, "revenue": 800.0, "location": "EU"},
        {"campaign_name": "Beta", "spend": 150.0, "conversions": 0, "revenue": 0.0, "location": "US"},
    ]
    df1 = pd.DataFrame(data)
    df2 = df1.sample(frac=1.0, random_state=42).reset_index(drop=True)

    insights1 = generate_insights(df=df1)
    insights2 = generate_insights(df=df2)

    assert insights1 == insights2

    # Check ID sequence
    ids = [i["id"] for i in insights1]
    assert ids == [f"insight-{idx:03d}" for idx in range(1, len(ids) + 1)]


def test_duplicate_and_contradiction_prevention():
    """12. Prevents single campaigns from being emitted as both best and worst."""
    data = [
        {"campaign_name": "Solo Campaign", "spend": 100.0, "conversions": 10, "revenue": 200.0}
    ]
    df = pd.DataFrame(data)
    insights = generate_insights(df=df)

    titles = [i["title"] for i in insights]
    # Should not have both lowest and highest CPA for the same single campaign
    assert "Lowest Cost per Acquisition: Solo Campaign" in titles
    assert "Highest Cost per Acquisition: Solo Campaign" not in titles

    # Should not have both highest and lowest ROAS for the same single campaign
    assert "Top Return on Ad Spend: Solo Campaign" in titles
    assert "Lowest Return on Ad Spend: Solo Campaign" not in titles


def test_strict_json_serialization_allow_nan_false():
    """13. All insight outputs serialize under strict JSON rules without NaN or Infinity."""
    data = [
        {"campaign_name": "Camp A", "spend": 0.0, "conversions": 0, "clicks": 0, "impressions": 0, "revenue": None, "location": "US"},
        {"campaign_name": "Camp B", "spend": 100.0, "conversions": 5, "clicks": 50, "impressions": 500, "revenue": 0.0, "location": "EU"},
    ]
    df = pd.DataFrame(data)
    insights = generate_insights(df=df)

    json_str = json.dumps(insights, allow_nan=False)
    assert isinstance(json_str, str)
    assert "NaN" not in json_str
    assert "Infinity" not in json_str

    parsed = json.loads(json_str)
    assert isinstance(parsed, list)


def test_backward_compatibility_with_cleaned_analytics_pipeline():
    """14. Seamless integration with clean_dataset and precomputed analytics outputs."""
    raw_campaigns = [
        {
            "campaign_name": "Campaign Alpha",
            "channel": "Google",
            "spend": 300.0,
            "conversions": 15,
            "clicks": 150,
            "impressions": 3000,
            "revenue": 900.0,
            "date": "2026-09-01",
            "location": "North America",
            "device": "Desktop",
        },
        {
            "campaign_name": "Campaign Beta",
            "channel": "Meta",
            "spend": 200.0,
            "conversions": 10,
            "clicks": 100,
            "impressions": 2000,
            "revenue": 400.0,
            "date": "2026-09-02",
            "location": "Europe",
            "device": "Mobile",
        },
    ]
    cleaned_df = clean_dataset(raw_campaigns)

    # Precalculate analytics as backend AnalysisService does
    kpis = calculate_kpis(cleaned_df)
    rankings = rank_campaigns(cleaned_df)
    trends = analyze_trends(cleaned_df)

    insights = generate_insights(kpis=kpis, rankings=rankings, trends=trends)

    assert isinstance(insights, list)
    assert len(insights) > 0
    # Every insight has contract keys
    for item in insights:
        assert "id" in item
        assert "type" in item
        assert "title" in item
        assert "description" in item
        assert "metric" in item
        assert "evidence" in item
