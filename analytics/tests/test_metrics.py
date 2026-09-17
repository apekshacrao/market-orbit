import pytest
import pandas as pd
import numpy as np

from analytics.kpi.metrics import calculate_kpis


# 1. Complete dataset
def test_kpis_complete_dataset():
    data = pd.DataFrame([
        {
            "campaign_name": "Campaign A",
            "channel": "Google Ads",
            "spend": 600.0,
            "conversions": 30,
            "clicks": 300,
            "impressions": 15000,
            "revenue": 1800.0,
        },
        {
            "campaign_name": "Campaign B",
            "channel": "Meta Ads",
            "spend": 400.0,
            "conversions": 20,
            "clicks": 200,
            "impressions": 10000,
            "revenue": 1200.0,
        },
    ])
    result = calculate_kpis(data)

    assert result["total_spend"] == 1000.0
    assert result["total_conversions"] == 50
    assert result["total_clicks"] == 500
    assert result["total_impressions"] == 25000
    assert result["total_revenue"] == 3000.0

    assert result["cpa"] == 20.0  # 1000 / 50
    assert result["cpc"] == 2.0   # 1000 / 500
    assert result["conversion_rate"] == 10.0  # (50 / 500) * 100
    assert result["ctr"] == 2.0   # (500 / 25000) * 100
    assert result["roas"] == 3.0  # 3000 / 1000
    assert result["roi"] == 200.0 # ((3000 - 1000) / 1000) * 100


# 2. Missing revenue
def test_kpis_missing_revenue():
    # Revenue column entirely missing
    data_no_col = pd.DataFrame([
        {
            "campaign_name": "Lead Gen",
            "channel": "LinkedIn",
            "spend": 800.0,
            "conversions": 40,
            "clicks": 400,
            "impressions": 20000,
        }
    ])
    result_no_col = calculate_kpis(data_no_col)
    assert result_no_col["total_revenue"] is None
    assert result_no_col["roas"] is None
    assert result_no_col["roi"] is None
    assert result_no_col["cpa"] == 20.0
    assert result_no_col["conversion_rate"] == 10.0

    # Revenue column present but all NaN
    data_nan = pd.DataFrame([
        {
            "campaign_name": "Lead Gen 2",
            "channel": "LinkedIn",
            "spend": 500.0,
            "conversions": 25,
            "clicks": 250,
            "impressions": 10000,
            "revenue": np.nan,
        }
    ])
    result_nan = calculate_kpis(data_nan)
    assert result_nan["total_revenue"] is None
    assert result_nan["roas"] is None
    assert result_nan["roi"] is None


# 3. Explicit zero revenue
def test_kpis_explicit_zero_revenue():
    data = pd.DataFrame([
        {
            "campaign_name": "Zero Return Push",
            "channel": "Meta Ads",
            "spend": 500.0,
            "conversions": 10,
            "clicks": 100,
            "impressions": 5000,
            "revenue": 0.0,
        }
    ])
    result = calculate_kpis(data)
    assert result["total_revenue"] == 0.0
    assert result["total_revenue"] is not None
    assert result["roas"] == 0.0
    assert result["roas"] is not None
    assert result["roi"] == -100.0  # ((0 - 500) / 500) * 100


# 4. Zero conversions
def test_cpa_zero_conversions():
    data = pd.DataFrame([
        {
            "campaign_name": "Brand Awareness",
            "channel": "YouTube",
            "spend": 600.0,
            "conversions": 0,
            "clicks": 200,
            "impressions": 50000,
            "revenue": None,
        }
    ])
    result = calculate_kpis(data)
    assert result["total_conversions"] == 0
    assert result["cpa"] == 0.0
    assert result["avg_cpa"] == 0.0


# 5. Zero clicks
def test_cpc_zero_clicks():
    data = pd.DataFrame([
        {
            "campaign_name": "Impression Only",
            "channel": "Display",
            "spend": 200.0,
            "conversions": 0,
            "clicks": 0,
            "impressions": 30000,
        }
    ])
    result = calculate_kpis(data)
    assert result["total_clicks"] == 0
    assert result["cpc"] == 0.0
    assert result["avg_cpc"] == 0.0


# 6. Conversion rate percentage scaling
def test_conversion_rate_percentage():
    data = pd.DataFrame([
        {
            "campaign_name": "Retargeting",
            "channel": "Google Ads",
            "spend": 300.0,
            "conversions": 25,
            "clicks": 500,
            "impressions": 10000,
        }
    ])
    result = calculate_kpis(data)
    # (25 / 500) * 100 = 5.0 (percentage, NOT 0.05)
    assert result["conversion_rate"] == 5.0
    assert result["avg_conversion_rate"] == 5.0


# 7. Zero clicks for conversion rate
def test_conversion_rate_zero_clicks():
    data = pd.DataFrame([
        {
            "campaign_name": "Zero Click Campaign",
            "channel": "Meta",
            "spend": 150.0,
            "conversions": 0,
            "clicks": 0,
            "impressions": 5000,
        }
    ])
    result = calculate_kpis(data)
    assert result["conversion_rate"] == 0.0
    assert result["avg_conversion_rate"] == 0.0


# 8. CTR percentage scaling
def test_ctr_percentage():
    data = pd.DataFrame([
        {
            "campaign_name": "Search Push",
            "channel": "Google Search",
            "spend": 450.0,
            "conversions": 20,
            "clicks": 150,
            "impressions": 10000,
        }
    ])
    result = calculate_kpis(data)
    # (150 / 10000) * 100 = 1.5 (percentage, NOT 0.015)
    assert result["ctr"] == 1.5


# 9. Zero impressions for CTR
def test_ctr_zero_impressions():
    data = pd.DataFrame([
        {
            "campaign_name": "Email Blast",
            "channel": "Email",
            "spend": 50.0,
            "conversions": 5,
            "clicks": 40,
            "impressions": 0,
        }
    ])
    result = calculate_kpis(data)
    assert result["ctr"] == 0.0


# 10. Positive and negative ROI
def test_roi_positive_and_negative():
    # Positive ROI: Revenue $2500, Spend $1000 -> ((2500 - 1000) / 1000) * 100 = 150.0%
    data_pos = pd.DataFrame([
        {
            "campaign_name": "High ROI Campaign",
            "channel": "Google",
            "spend": 1000.0,
            "conversions": 50,
            "revenue": 2500.0,
        }
    ])
    result_pos = calculate_kpis(data_pos)
    assert result_pos["roi"] == 150.0
    assert result_pos["roas"] == 2.5

    # Negative ROI: Revenue $400, Spend $1000 -> ((400 - 1000) / 1000) * 100 = -60.0%
    data_neg = pd.DataFrame([
        {
            "campaign_name": "Low ROI Campaign",
            "channel": "Meta",
            "spend": 1000.0,
            "conversions": 10,
            "revenue": 400.0,
        }
    ])
    result_neg = calculate_kpis(data_neg)
    assert result_neg["roi"] == -60.0
    assert result_neg["roas"] == 0.4


# 11. Backward-compatible aliases
def test_backward_compatible_aliases():
    data = pd.DataFrame([
        {
            "campaign_name": "Test Aliases",
            "channel": "Omnichannel",
            "spend": 500.0,
            "conversions": 25,
            "clicks": 250,
            "impressions": 12500,
            "revenue": 1500.0,
        }
    ])
    result = calculate_kpis(data)

    assert result["avg_cpa"] == result["cpa"]
    assert result["avg_cpc"] == result["cpc"]
    assert result["avg_conversion_rate"] == result["conversion_rate"]
    assert result["overall_roas"] == result["roas"]


# 12. Empty DataFrame
def test_empty_dataframe():
    df_empty = pd.DataFrame()
    result = calculate_kpis(df_empty)

    assert result["total_spend"] == 0.0
    assert result["total_conversions"] == 0
    assert result["total_clicks"] == 0
    assert result["total_impressions"] == 0
    assert result["total_revenue"] is None

    assert result["cpa"] == 0.0
    assert result["avg_cpa"] == 0.0
    assert result["cpc"] == 0.0
    assert result["avg_cpc"] == 0.0
    assert result["conversion_rate"] == 0.0
    assert result["avg_conversion_rate"] == 0.0
    assert result["ctr"] == 0.0
    assert result["roas"] is None
    assert result["overall_roas"] is None
    assert result["roi"] is None
