import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def _parse_valid_date(val: Any) -> Optional[datetime.date]:
    """Parses a date string, datetime.date, or datetime.datetime to a valid calendar date."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "nat"):
        return None
    try:
        dt = datetime.datetime.strptime(s, "%Y-%m-%d")
        return dt.date()
    except (ValueError, TypeError):
        return None


def _aggregate_daily_records(date_str: str, group: pd.DataFrame) -> Dict[str, Any]:
    """Aggregates performance metrics for a single calendar date."""
    spend = (
        round(float(pd.to_numeric(group["spend"], errors="coerce").fillna(0.0).sum()), 2)
        if "spend" in group.columns
        else 0.0
    )
    conversions = (
        int(pd.to_numeric(group["conversions"], errors="coerce").fillna(0).sum())
        if "conversions" in group.columns
        else 0
    )
    clicks = (
        int(pd.to_numeric(group["clicks"], errors="coerce").fillna(0).sum())
        if "clicks" in group.columns
        else 0
    )
    impressions = (
        int(pd.to_numeric(group["impressions"], errors="coerce").fillna(0).sum())
        if "impressions" in group.columns
        else 0
    )

    revenue: Optional[float] = None
    if "revenue" in group.columns:
        rev_series = group["revenue"]
        if rev_series.isna().all() or rev_series.isna().any():
            revenue = None
        else:
            rev_num = pd.to_numeric(rev_series, errors="coerce")
            if rev_num.isna().any():
                revenue = None
            else:
                revenue = round(float(rev_num.sum()), 2)

    cpa: Optional[float] = (
        round(float(spend / conversions), 2) if conversions > 0 else None
    )
    cpc: Optional[float] = (
        round(float(spend / clicks), 2) if clicks > 0 else None
    )
    ctr: Optional[float] = (
        round(float((clicks / impressions) * 100.0), 2) if impressions > 0 else None
    )
    conversion_rate: Optional[float] = (
        round(float((conversions / clicks) * 100.0), 2) if clicks > 0 else None
    )
    roas: Optional[float] = (
        round(float(revenue / spend), 2)
        if revenue is not None and spend > 0.0
        else None
    )
    roi: Optional[float] = (
        round(float(((revenue - spend) / spend) * 100.0), 2)
        if revenue is not None and spend > 0.0
        else None
    )

    return {
        "date": date_str,
        "spend": spend,
        "conversions": conversions,
        "clicks": clicks,
        "impressions": impressions,
        "revenue": revenue,
        "cpa": cpa,
        "cpc": cpc,
        "ctr": ctr,
        "conversion_rate": conversion_rate,
        "roas": roas,
        "roi": roi,
    }


def analyze_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes historical performance trends across channels and chronological time series.

    Returns:
        Dict with:
        - 'channel_breakdown': aggregations grouped by channel (backward-compatible).
        - 'time_series': chronological timeline, date range, availability status, and daily metrics.
    """
    insufficient_time_series = {
        "has_time_series": False,
        "status": "insufficient_data",
        "start_date": None,
        "end_date": None,
        "date_range": {
            "start": None,
            "end": None,
            "total_days": 0,
        },
        "distinct_dates_count": 0,
        "timeline": [],
    }

    if df is None or df.empty:
        return {
            "channel_breakdown": {},
            "time_series": insufficient_time_series,
        }

    # 1. Existing Channel Breakdown (backward-compatible)
    channel_trends = {}
    if "channel" in df.columns:
        for channel, group in df.groupby("channel", sort=True):
            channel_name = str(channel).strip()
            if not channel_name or channel_name.lower() == "nan":
                continue
            spend = (
                round(float(pd.to_numeric(group["spend"], errors="coerce").fillna(0.0).sum()), 2)
                if "spend" in group.columns
                else 0.0
            )
            conversions = (
                int(pd.to_numeric(group["conversions"], errors="coerce").fillna(0).sum())
                if "conversions" in group.columns
                else 0
            )
            if "revenue" not in group.columns:
                revenue = None
            elif group["revenue"].isna().all() or group["revenue"].isna().any():
                revenue = None
            else:
                rev_num = pd.to_numeric(group["revenue"], errors="coerce")
                revenue = None if rev_num.isna().any() else round(float(rev_num.sum()), 2)

            channel_trends[channel_name] = {
                "spend": spend,
                "revenue": revenue,
                "conversions": conversions,
            }

    # 2. Chronological Time-Series Analysis
    if "date" not in df.columns:
        return {
            "channel_breakdown": channel_trends,
            "time_series": insufficient_time_series,
        }

    # Parse and validate dates
    parsed_dates = df["date"].apply(_parse_valid_date)
    valid_mask = parsed_dates.notna()

    if not valid_mask.any():
        return {
            "channel_breakdown": channel_trends,
            "time_series": insufficient_time_series,
        }

    valid_df = df[valid_mask].copy()
    valid_df["_parsed_date"] = parsed_dates[valid_mask]

    # Group by parsed date and sort chronologically
    grouped_by_date = {
        d: grp for d, grp in valid_df.groupby("_parsed_date", sort=True)
    }

    distinct_dates = sorted(grouped_by_date.keys())
    distinct_dates_count = len(distinct_dates)

    # Require at least 2 distinct valid calendar dates
    if distinct_dates_count < 2:
        return {
            "channel_breakdown": channel_trends,
            "time_series": {
                "has_time_series": False,
                "status": "insufficient_data",
                "start_date": None,
                "end_date": None,
                "date_range": {
                    "start": None,
                    "end": None,
                    "total_days": 0,
                },
                "distinct_dates_count": distinct_dates_count,
                "timeline": [],
            },
        }

    start_date_obj = distinct_dates[0]
    end_date_obj = distinct_dates[-1]
    start_date_str = start_date_obj.strftime("%Y-%m-%d")
    end_date_str = end_date_obj.strftime("%Y-%m-%d")
    total_days = (end_date_obj - start_date_obj).days + 1

    timeline: List[Dict[str, Any]] = [
        _aggregate_daily_records(d.strftime("%Y-%m-%d"), grouped_by_date[d])
        for d in distinct_dates
    ]

    time_series_data = {
        "has_time_series": True,
        "status": "available",
        "start_date": start_date_str,
        "end_date": end_date_str,
        "date_range": {
            "start": start_date_str,
            "end": end_date_str,
            "total_days": total_days,
        },
        "distinct_dates_count": distinct_dates_count,
        "timeline": timeline,
    }

    return {
        "channel_breakdown": channel_trends,
        "time_series": time_series_data,
    }

