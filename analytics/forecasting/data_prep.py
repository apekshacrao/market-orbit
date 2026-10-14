"""
Forecasting data preprocessing and time-series regularization for Market Orbit.

Prepares chronological daily series of additive metrics (spend, conversions, clicks,
impressions, revenue) and computes data-quality coverage diagnostics for downstream
forecasting models.
"""

import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from analytics.trends.customer_trends import _parse_valid_date


def prepare_daily_series(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates, aggregates, and prepares a daily chronological time series of additive
    metrics with historical coverage diagnostics for time-series forecasting.

    Args:
        df: Pandas DataFrame containing marketing records with optional 'date',
            'spend', 'conversions', 'clicks', 'impressions', and 'revenue'.

    Returns:
        Dict with:
        - 'is_available': bool indicating whether at least one valid daily record was prepared.
        - 'status': str diagnostic status ('ready', 'insufficient_history', 'non_contiguous',
                    'no_valid_dates', or 'unavailable').
        - 'metadata': dict of date counts, date ranges, contiguous streaks, and coverage flags.
        - 'series': list of daily aggregated records with additive metrics and 'is_observed' flag.
        - 'revenue_complete': bool indicating if revenue tracking is complete across all valid dates.
        - 'warnings': list of descriptive data-quality warnings.
    """
    empty_metadata = {
        "historical_dates_count": 0,
        "start_date": None,
        "end_date": None,
        "calendar_span_days": 0,
        "contiguous_dates_count": 0,
        "max_contiguous_streak": 0,
        "missing_dates_count": 0,
        "is_contiguous": False,
        "has_minimum_dates": False,
        "has_seasonal_dates": False,
        "excluded_records_count": 0,
        "total_records_count": 0,
    }

    if df is None or df.empty or "date" not in df.columns:
        return {
            "is_available": False,
            "status": "unavailable",
            "metadata": empty_metadata,
            "series": [],
            "revenue_complete": False,
            "warnings": ["Dataset is empty or missing mandatory 'date' column."],
        }

    total_records = len(df)

    # 1. Strict YYYY-MM-DD Date Parsing
    parsed_dates = df["date"].apply(_parse_valid_date)
    valid_mask = parsed_dates.notna()
    valid_records_count = int(valid_mask.sum())
    excluded_records_count = total_records - valid_records_count

    warnings: List[str] = []
    if excluded_records_count > 0:
        warnings.append(
            f"Excluded {excluded_records_count} record(s) with missing or invalid date format."
        )

    if valid_records_count == 0:
        empty_metadata["excluded_records_count"] = excluded_records_count
        empty_metadata["total_records_count"] = total_records
        return {
            "is_available": False,
            "status": "no_valid_dates",
            "metadata": empty_metadata,
            "series": [],
            "revenue_complete": False,
            "warnings": warnings + ["No valid calendar dates (YYYY-MM-DD) found in dataset."],
        }

    # 2. Chronological Grouping on Valid Records (Caller DataFrame is not mutated)
    valid_df = df[valid_mask].copy()
    valid_df["_parsed_date"] = parsed_dates[valid_mask].values

    # Determine overall revenue completeness across all valid-date rows
    revenue_complete = False
    if "revenue" in valid_df.columns:
        rev_series = valid_df["revenue"]
        if not rev_series.isna().all() and not rev_series.isna().any():
            rev_num = pd.to_numeric(rev_series, errors="coerce")
            if not rev_num.isna().any():
                revenue_complete = True

    if not revenue_complete:
        if "revenue" not in valid_df.columns or valid_df["revenue"].isna().all():
            warnings.append("Revenue tracking is unavailable in historical data.")
        else:
            warnings.append(
                "Revenue tracking is partially missing or unparseable; revenue metrics will remain unavailable."
            )

    # Group records by calendar date
    grouped_by_date = {
        d: grp for d, grp in valid_df.groupby("_parsed_date", sort=True)
    }
    distinct_dates: List[datetime.date] = sorted(grouped_by_date.keys())
    historical_dates_count = len(distinct_dates)

    start_date_obj = distinct_dates[0]
    end_date_obj = distinct_dates[-1]
    start_date_str = start_date_obj.strftime("%Y-%m-%d")
    end_date_str = end_date_obj.strftime("%Y-%m-%d")
    calendar_span_days = (end_date_obj - start_date_obj).days + 1
    missing_dates_count = calendar_span_days - historical_dates_count

    # 3. Calculate Longest Contiguous Date Streak
    max_streak = 1
    current_streak = 1
    for i in range(1, historical_dates_count):
        if (distinct_dates[i] - distinct_dates[i - 1]).days == 1:
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
        else:
            current_streak = 1

    is_contiguous = (missing_dates_count == 0)
    has_minimum_dates = (historical_dates_count >= 7)
    has_seasonal_dates = (max_streak >= 14)

    if not is_contiguous:
        warnings.append(
            f"Timeline contains {missing_dates_count} unobserved calendar date(s) between "
            f"{start_date_str} and {end_date_str}; unobserved dates are not assumed to have zero activity."
        )

    if not has_minimum_dates:
        warnings.append(
            f"Historical series contains {historical_dates_count} distinct date(s); "
            f"minimum 7 distinct daily observations required for reliable forecasting."
        )

    # Determine status
    if not has_minimum_dates:
        status = "insufficient_history"
    elif not is_contiguous:
        status = "non_contiguous"
    else:
        status = "ready"

    # 4. Aggregate Daily Additive Metrics for Observed Dates
    series: List[Dict[str, Any]] = []
    for d in distinct_dates:
        grp = grouped_by_date[d]
        date_str = d.strftime("%Y-%m-%d")

        spend = (
            round(float(pd.to_numeric(grp["spend"], errors="coerce").fillna(0.0).sum()), 2)
            if "spend" in grp.columns
            else 0.0
        )
        conversions = (
            int(pd.to_numeric(grp["conversions"], errors="coerce").fillna(0).sum())
            if "conversions" in grp.columns
            else 0
        )
        clicks = (
            int(pd.to_numeric(grp["clicks"], errors="coerce").fillna(0).sum())
            if "clicks" in grp.columns
            else 0
        )
        impressions = (
            int(pd.to_numeric(grp["impressions"], errors="coerce").fillna(0).sum())
            if "impressions" in grp.columns
            else 0
        )

        # Revenue aggregation per date: only populate if all rows for this date have valid numbers
        date_revenue: Optional[float] = None
        if "revenue" in grp.columns:
            s_rev = grp["revenue"]
            if not s_rev.isna().all() and not s_rev.isna().any():
                s_rev_num = pd.to_numeric(s_rev, errors="coerce")
                if not s_rev_num.isna().any():
                    date_revenue = round(float(s_rev_num.sum()), 2)

        series.append({
            "date": date_str,
            "spend": spend,
            "conversions": conversions,
            "clicks": clicks,
            "impressions": impressions,
            "revenue": date_revenue,
            "is_observed": True,
        })

    metadata = {
        "historical_dates_count": historical_dates_count,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "calendar_span_days": calendar_span_days,
        "contiguous_dates_count": max_streak,
        "max_contiguous_streak": max_streak,
        "missing_dates_count": missing_dates_count,
        "is_contiguous": is_contiguous,
        "has_minimum_dates": has_minimum_dates,
        "has_seasonal_dates": has_seasonal_dates,
        "excluded_records_count": excluded_records_count,
        "total_records_count": total_records,
    }

    return {
        "is_available": True,
        "status": status,
        "metadata": metadata,
        "series": series,
        "revenue_complete": revenue_complete,
        "warnings": warnings,
    }
