"""
Deterministic baseline forecasting models for Market Orbit analytics.

Implements three foundational time-series baselines on prepared daily series:
1. Naive persistence baseline (latest observed value)
2. Simple moving average (7-day rolling mean)
3. 7-day seasonal naive (weekly cycle persistence)

All forecasts operate exclusively on additive metrics (spend, conversions, clicks,
impressions, revenue) and adhere to strict date-continuity and revenue-completeness guards.
"""

import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from analytics.forecasting.data_prep import prepare_daily_series, SUPPORTED_METRICS


def _check_contiguous_range(dates: List[datetime.date]) -> bool:
    """Returns True if the list of sorted datetime.date objects is strictly contiguous."""
    if not dates:
        return False
    if len(dates) == 1:
        return True
    if (dates[-1] - dates[0]).days != len(dates) - 1:
        return False
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days != 1:
            return False
    return True


def forecast_baselines(df: pd.DataFrame, horizon: int = 7) -> Dict[str, Any]:
    """
    Generates deterministic baseline time-series forecasts across additive metrics.

    Consumes prepare_daily_series() as its input boundary, evaluates eligibility
    for each baseline model, and projects exactly `horizon` future daily points.

    Args:
        df: Pandas DataFrame containing historical campaign records.
        horizon: Positive integer number of calendar days to forecast ahead (default 7).

    Returns:
        Dict with:
        - 'is_available': bool indicating whether baseline forecasts were produced.
        - 'status': str diagnostic status ('ready', 'ready_basic', 'insufficient_history', or 'unavailable').
        - 'horizon': int forecast horizon in calendar days.
        - 'metadata': historical coverage and forecast date range diagnostics.
        - 'models': dict containing forecast outputs and eligibility for:
            - 'naive': persistence baseline
            - 'sma_7': 7-day simple moving average
            - 'seasonal_naive': 7-day weekly cycle naive
        - 'revenue_complete': bool indicating if revenue forecasting was supported.
        - 'warnings': list of diagnostic warnings.

    Raises:
        ValueError: If horizon is not a positive integer (e.g. booleans, <=0, strings, floats).
    """
    # 1. Parameter Validation
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0:
        raise ValueError(f"Forecast horizon must be a positive integer, got {horizon!r}")

    # 2. Daily Series Preprocessing
    prep = prepare_daily_series(df)
    prep_meta = prep["metadata"]
    series = prep["series"]
    warnings: List[str] = list(prep["warnings"])
    revenue_complete = prep["revenue_complete"]

    ineligibility_msg = "Insufficient historical observations; minimum 7 distinct daily records required."
    snaive_ineligibility_msg = "Seasonal naive requires at least 14 contiguous calendar days immediately preceding the forecast horizon."

    empty_result: Dict[str, Any] = {
        "is_available": False,
        "status": prep["status"] if not prep["is_available"] else "insufficient_history",
        "horizon": horizon,
        "metadata": {
            "start_date": prep_meta["start_date"],
            "end_date": prep_meta["end_date"],
            "forecast_start_date": None,
            "forecast_end_date": None,
            "historical_dates_count": prep_meta["historical_dates_count"],
            "calendar_span_days": prep_meta["calendar_span_days"],
            "is_contiguous": prep_meta["is_contiguous"],
            "contiguous_dates_count": prep_meta["contiguous_dates_count"],
            "has_minimum_dates": prep_meta["has_minimum_dates"],
            "has_seasonal_dates": prep_meta["has_seasonal_dates"],
            "revenue_complete": revenue_complete,
        },
        "models": {
            "naive": {
                "is_eligible": False,
                "model_name": "naive_persistence",
                "forecast": [],
                "ineligibility_reason": ineligibility_msg,
                "metric_status": {m: "ineligible" for m in SUPPORTED_METRICS},
                "metric_reasons": {m: ineligibility_msg for m in SUPPORTED_METRICS},
            },
            "sma_7": {
                "is_eligible": False,
                "model_name": "simple_moving_average_7d",
                "forecast": [],
                "ineligibility_reason": ineligibility_msg,
                "metric_status": {m: "ineligible" for m in SUPPORTED_METRICS},
                "metric_reasons": {m: ineligibility_msg for m in SUPPORTED_METRICS},
            },
            "seasonal_naive": {
                "is_eligible": False,
                "model_name": "seasonal_naive_7d",
                "forecast": [],
                "ineligibility_reason": snaive_ineligibility_msg,
                "metric_status": {m: "ineligible" for m in SUPPORTED_METRICS},
                "metric_reasons": {m: snaive_ineligibility_msg for m in SUPPORTED_METRICS},
            },
        },
        "revenue_complete": revenue_complete,
        "warnings": warnings,
    }

    # Minimum threshold: require at least 7 distinct historical dates for any baseline forecasting
    if not prep["is_available"] or prep_meta["historical_dates_count"] < 7:
        return empty_result

    # 3. Forecast Dates Construction
    last_date_obj = datetime.datetime.strptime(prep_meta["end_date"], "%Y-%m-%d").date()
    forecast_dates: List[str] = [
        (last_date_obj + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(1, horizon + 1)
    ]
    forecast_start_date = forecast_dates[0]
    forecast_end_date = forecast_dates[-1]

    # Revenue forecast policy: if historical revenue incomplete, revenue forecast is strictly None
    if not revenue_complete:
        warnings.append(
            "Revenue forecasting is unavailable because historical revenue tracking is incomplete or untracked."
        )

    # 4. Model 1: Naive Persistence Baseline
    last_obs = series[-1]
    naive_metric_status: Dict[str, str] = {}
    naive_metric_reasons: Dict[str, Optional[str]] = {}
    naive_values: Dict[str, Any] = {}

    for m in SUPPORTED_METRICS:
        if m == "revenue":
            if revenue_complete and last_obs["revenue"] is not None:
                naive_metric_status["revenue"] = "available"
                naive_metric_reasons["revenue"] = None
                naive_values["revenue"] = round(float(max(0.0, last_obs["revenue"])), 2)
            else:
                naive_metric_status["revenue"] = "unavailable"
                naive_metric_reasons["revenue"] = (
                    "Revenue tracking is incomplete, untracked, or invalid in historical observations."
                )
                naive_values["revenue"] = None
        elif m == "spend":
            if last_obs["spend"] is not None:
                naive_metric_status["spend"] = "available"
                naive_metric_reasons["spend"] = None
                naive_values["spend"] = round(float(max(0.0, last_obs["spend"])), 2)
            else:
                naive_metric_status["spend"] = "unavailable"
                naive_metric_reasons["spend"] = (
                    "Spend metric is untracked, missing, or invalid in the latest observation."
                )
                naive_values["spend"] = None
        else:  # count metrics: conversions, clicks, impressions
            if last_obs[m] is not None:
                naive_metric_status[m] = "available"
                naive_metric_reasons[m] = None
                naive_values[m] = int(max(0, last_obs[m]))
            else:
                naive_metric_status[m] = "unavailable"
                naive_metric_reasons[m] = (
                    f"Metric '{m}' is untracked, missing, or invalid in the latest observation."
                )
                naive_values[m] = None

    naive_forecast: List[Dict[str, Any]] = []
    for f_date in forecast_dates:
        naive_forecast.append({
            "date": f_date,
            "spend": naive_values["spend"],
            "conversions": naive_values["conversions"],
            "clicks": naive_values["clicks"],
            "impressions": naive_values["impressions"],
            "revenue": naive_values["revenue"],
        })

    # 5. Model 2: Simple Moving Average (SMA-7)
    sma_eligible = len(series) >= 7
    sma_forecast: List[Dict[str, Any]] = []
    sma_reason: Optional[str] = None
    sma_metric_status: Dict[str, str] = {}
    sma_metric_reasons: Dict[str, Optional[str]] = {}
    sma_values: Dict[str, Any] = {}

    if sma_eligible:
        sma_window = series[-7:]
        # Require seven consecutive calendar dates immediately preceding the forecast origin
        window_dates = [
            datetime.datetime.strptime(row["date"], "%Y-%m-%d").date()
            for row in sma_window
        ]
        window_contiguous = _check_contiguous_range(window_dates)
        if not window_contiguous:
            sma_eligible = False
            sma_reason = (
                "SMA-7 requires 7 consecutive calendar dates immediately preceding the forecast origin; "
                "calendar gaps detected in the recent 7-day window."
            )
            sma_metric_status = {m: "ineligible" for m in SUPPORTED_METRICS}
            sma_metric_reasons = {m: sma_reason for m in SUPPORTED_METRICS}
            warnings.append(sma_reason)
        else:
            # 7 contiguous days confirmed; evaluate usability for each metric individually
            for m in SUPPORTED_METRICS:
                if m == "revenue":
                    if not revenue_complete:
                        sma_metric_status["revenue"] = "unavailable"
                        sma_metric_reasons["revenue"] = (
                            "Revenue tracking is incomplete, untracked, or invalid in historical observations."
                        )
                        sma_values["revenue"] = None
                    else:
                        rev_vals = [r["revenue"] for r in sma_window]
                        if any(v is None for v in rev_vals):
                            sma_metric_status["revenue"] = "unavailable"
                            sma_metric_reasons["revenue"] = (
                                "SMA-7 forecast for 'revenue' is unavailable due to missing or invalid observations in the recent 7-day window."
                            )
                            sma_values["revenue"] = None
                        else:
                            sma_metric_status["revenue"] = "available"
                            sma_metric_reasons["revenue"] = None
                            sma_values["revenue"] = round(float(sum(rev_vals) / 7.0), 2)
                elif m == "spend":
                    spend_vals = [r["spend"] for r in sma_window]
                    if any(v is None for v in spend_vals):
                        sma_metric_status["spend"] = "unavailable"
                        sma_metric_reasons["spend"] = (
                            "SMA-7 forecast for 'spend' is unavailable due to missing or invalid observations in the recent 7-day window."
                        )
                        sma_values["spend"] = None
                        warnings.append("SMA-7 forecast for 'spend' is unavailable due to missing or invalid observations in the recent 7-day window.")
                    else:
                        sma_metric_status["spend"] = "available"
                        sma_metric_reasons["spend"] = None
                        sma_values["spend"] = round(float(sum(spend_vals) / 7.0), 2)
                else:  # count metrics: conversions, clicks, impressions
                    count_vals = [r[m] for r in sma_window]
                    if any(v is None for v in count_vals):
                        sma_metric_status[m] = "unavailable"
                        sma_metric_reasons[m] = (
                            f"SMA-7 forecast for '{m}' is unavailable due to missing or invalid observations in the recent 7-day window."
                        )
                        sma_values[m] = None
                        warnings.append(f"SMA-7 forecast for '{m}' is unavailable due to missing or invalid observations in the recent 7-day window.")
                    else:
                        # Count metric rounding policy: standard round-half-to-even via Python's round(),
                        # clamped to non-negative integer int(max(0, round(mean_val))).
                        mean_count = sum(count_vals) / 7.0
                        sma_metric_status[m] = "available"
                        sma_metric_reasons[m] = None
                        sma_values[m] = int(max(0, round(mean_count)))

            for f_date in forecast_dates:
                sma_forecast.append({
                    "date": f_date,
                    "spend": sma_values["spend"],
                    "conversions": sma_values["conversions"],
                    "clicks": sma_values["clicks"],
                    "impressions": sma_values["impressions"],
                    "revenue": sma_values["revenue"],
                })
    else:
        sma_reason = "SMA-7 requires at least 7 historical daily observations."
        sma_metric_status = {m: "ineligible" for m in SUPPORTED_METRICS}
        sma_metric_reasons = {m: sma_reason for m in SUPPORTED_METRICS}

    # 6. Model 3: Seven-Day Seasonal Naive (SNaive-7)
    # Strictly requires at least 14 observed dates AND that the most recent 14 dates are genuinely contiguous
    snaive_eligible = False
    snaive_forecast: List[Dict[str, Any]] = []
    snaive_reason: Optional[str] = None
    snaive_metric_status: Dict[str, str] = {}
    snaive_metric_reasons: Dict[str, Optional[str]] = {}

    if len(series) >= 14:
        recent_14 = series[-14:]
        dates_14 = [
            datetime.datetime.strptime(row["date"], "%Y-%m-%d").date()
            for row in recent_14
        ]
        is_recent_14_contiguous = _check_contiguous_range(dates_14)

        if is_recent_14_contiguous:
            snaive_eligible = True
            recent_7 = series[-7:]

            # Evaluate usability across the 7-day seasonal cycle for each metric
            for m in SUPPORTED_METRICS:
                if m == "revenue":
                    if not revenue_complete or any(r["revenue"] is None for r in recent_7):
                        snaive_metric_status["revenue"] = "unavailable"
                        snaive_metric_reasons["revenue"] = (
                            "Revenue tracking is incomplete, untracked, or invalid across the 7-day seasonal cycle."
                        )
                    else:
                        snaive_metric_status["revenue"] = "available"
                        snaive_metric_reasons["revenue"] = None
                elif m == "spend":
                    if any(r["spend"] is None for r in recent_7):
                        snaive_metric_status["spend"] = "unavailable"
                        snaive_metric_reasons["spend"] = (
                            "Spend metric has missing or invalid observations across the 7-day seasonal cycle."
                        )
                    else:
                        snaive_metric_status["spend"] = "available"
                        snaive_metric_reasons["spend"] = None
                else:  # count metrics
                    if any(r[m] is None for r in recent_7):
                        snaive_metric_status[m] = "unavailable"
                        snaive_metric_reasons[m] = (
                            f"Metric '{m}' has missing or invalid observations across the 7-day seasonal cycle."
                        )
                    else:
                        snaive_metric_status[m] = "available"
                        snaive_metric_reasons[m] = None

            for step_idx, f_date in enumerate(forecast_dates):
                # Cycle index for the corresponding weekday: (step_idx % 7) maps to recent_7
                source_day = recent_7[step_idx % 7]
                snaive_forecast.append({
                    "date": f_date,
                    "spend": (
                        round(float(max(0.0, source_day["spend"])), 2)
                        if snaive_metric_status["spend"] == "available" and source_day["spend"] is not None
                        else None
                    ),
                    "conversions": (
                        int(max(0, source_day["conversions"]))
                        if snaive_metric_status["conversions"] == "available" and source_day["conversions"] is not None
                        else None
                    ),
                    "clicks": (
                        int(max(0, source_day["clicks"]))
                        if snaive_metric_status["clicks"] == "available" and source_day["clicks"] is not None
                        else None
                    ),
                    "impressions": (
                        int(max(0, source_day["impressions"]))
                        if snaive_metric_status["impressions"] == "available" and source_day["impressions"] is not None
                        else None
                    ),
                    "revenue": (
                        round(float(max(0.0, source_day["revenue"])), 2)
                        if snaive_metric_status["revenue"] == "available" and source_day["revenue"] is not None
                        else None
                    ),
                })
        else:
            snaive_reason = (
                "Seasonal naive requires at least 14 contiguous calendar days immediately preceding "
                "the forecast horizon; unobserved calendar gaps exist within the recent 14 days."
            )
            snaive_metric_status = {m: "ineligible" for m in SUPPORTED_METRICS}
            snaive_metric_reasons = {m: snaive_reason for m in SUPPORTED_METRICS}
    else:
        snaive_reason = (
            f"Seasonal naive requires at least 14 contiguous daily observations; "
            f"dataset only has {len(series)} observed dates."
        )
        snaive_metric_status = {m: "ineligible" for m in SUPPORTED_METRICS}
        snaive_metric_reasons = {m: snaive_reason for m in SUPPORTED_METRICS}

    # 7. Final Response Assembly
    return {
        "is_available": True,
        "status": "ready" if snaive_eligible else "ready_basic",
        "horizon": horizon,
        "metadata": {
            "start_date": prep_meta["start_date"],
            "end_date": prep_meta["end_date"],
            "forecast_start_date": forecast_start_date,
            "forecast_end_date": forecast_end_date,
            "historical_dates_count": prep_meta["historical_dates_count"],
            "calendar_span_days": prep_meta["calendar_span_days"],
            "is_contiguous": prep_meta["is_contiguous"],
            "contiguous_dates_count": prep_meta["contiguous_dates_count"],
            "has_minimum_dates": prep_meta["has_minimum_dates"],
            "has_seasonal_dates": snaive_eligible,
            "revenue_complete": revenue_complete,
        },
        "models": {
            "naive": {
                "is_eligible": True,
                "model_name": "naive_persistence",
                "forecast": naive_forecast,
                "ineligibility_reason": None,
                "metric_status": naive_metric_status,
                "metric_reasons": naive_metric_reasons,
            },
            "sma_7": {
                "is_eligible": sma_eligible,
                "model_name": "simple_moving_average_7d",
                "forecast": sma_forecast,
                "ineligibility_reason": sma_reason,
                "metric_status": sma_metric_status,
                "metric_reasons": sma_metric_reasons,
            },
            "seasonal_naive": {
                "is_eligible": snaive_eligible,
                "model_name": "seasonal_naive_7d",
                "forecast": snaive_forecast,
                "ineligibility_reason": snaive_reason,
                "metric_status": snaive_metric_status,
                "metric_reasons": snaive_metric_reasons,
            },
        },
        "revenue_complete": revenue_complete,
        "warnings": warnings,
    }
