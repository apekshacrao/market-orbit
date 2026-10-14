"""
Consolidated public forecasting orchestration service for Market Orbit.

Unifies preprocessing (Phase 4.1), baseline projections (Phase 4.2/4.2.1), and
walk-forward temporal validation (Phase 4.3/4.3.1) behind a clean, deterministic,
leakage-safe public interface.
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from analytics.forecasting.data_prep import (
    prepare_daily_series,
    SUPPORTED_METRICS,
)
from analytics.forecasting.baselines import forecast_baselines
from analytics.forecasting.validation import validate_baselines, _validate_positive_int


def run_forecasting_analysis(
    df: pd.DataFrame,
    horizon: int = 7,
    min_train_dates: int = 14,
    step: int = 1,
) -> Dict[str, Any]:
    """
    Executes the consolidated Market Orbit forecasting workflow.

    Orchestrates:
    1. Daily series regularization and historical coverage diagnostics (prepare_daily_series).
    2. Deterministic baseline forecasting across additive metrics (forecast_baselines).
    3. Leakage-safe walk-forward temporal error evaluation (validate_baselines).

    Args:
        df: Pandas DataFrame containing historical marketing records with 'date' and
            optional additive metrics (spend, conversions, clicks, impressions, revenue).
        horizon: Positive integer number of calendar days to forecast ahead (default 7).
        min_train_dates: Positive integer minimum number of distinct historical dates
            required for the initial walk-forward training split (default 14).
        step: Positive integer number of observed calendar dates to advance the
            forecast origin between walk-forward splits (default 1).

    Returns:
        Dict with:
        - 'is_available': bool indicating whether forecasting analysis was produced.
        - 'status': str deterministic status ('ready', 'ready_basic', 'ready_forecast_only',
                    'ready_basic_forecast_only', 'insufficient_history', 'no_valid_dates',
                    or 'unavailable').
        - 'parameters': dict of validated parameters (horizon, min_train_dates, step).
        - 'historical_coverage': dict of timeline and data-quality coverage diagnostics.
        - 'forecasts': dict containing baseline model forecasts and eligibility.
        - 'validation': dict containing walk-forward evaluation errors and origins.
        - 'revenue_complete': bool indicating if revenue tracking is fully complete.
        - 'warnings': list of deduplicated diagnostic warnings.

    Raises:
        ValueError: If horizon, min_train_dates, or step is not a positive integer.
    """
    # 1. Parameter Validation
    horizon = _validate_positive_int(horizon, "Forecast horizon")
    min_train_dates = _validate_positive_int(min_train_dates, "min_train_dates")
    step = _validate_positive_int(step, "step")

    # 2. Daily Series Preprocessing
    prep_res = prepare_daily_series(df)
    prep_meta = prep_res["metadata"]
    revenue_complete = prep_res["revenue_complete"]

    # 3. Baseline Projections & Walk-Forward Validation
    forecast_res = forecast_baselines(df, horizon=horizon)
    val_res = validate_baselines(
        df,
        horizon=horizon,
        min_train_dates=min_train_dates,
        step=step,
    )

    # 4. Deterministic Overall Status Determination
    # Preprocessing availability is the foundational gate
    if not prep_res["is_available"]:
        is_available = False
        status = prep_res["status"]  # 'unavailable' or 'no_valid_dates'
    elif not forecast_res["is_available"]:
        # Preprocessing has valid dates, but fewer than 7 distinct dates
        is_available = False
        status = "insufficient_history"
    else:
        # Forecasts are available (historical_dates_count >= 7)
        is_available = True
        forecast_status = forecast_res["status"]  # 'ready' (seasonal eligible) or 'ready_basic'
        validation_available = val_res["is_available"]

        if forecast_status == "ready":
            status = "ready" if validation_available else "ready_forecast_only"
        else:  # 'ready_basic'
            status = "ready_basic" if validation_available else "ready_basic_forecast_only"

    # 5. Deduplicated Diagnostic Warnings Assembly
    combined_warnings: List[str] = []
    seen_warnings = set()
    for w in prep_res["warnings"] + forecast_res["warnings"] + val_res["warnings"]:
        if w not in seen_warnings:
            combined_warnings.append(w)
            seen_warnings.add(w)

    # 6. Response Structure Assembly
    return {
        "is_available": is_available,
        "status": status,
        "parameters": {
            "horizon": horizon,
            "min_train_dates": min_train_dates,
            "step": step,
        },
        "historical_coverage": {
            "start_date": prep_meta["start_date"],
            "end_date": prep_meta["end_date"],
            "historical_dates_count": prep_meta["historical_dates_count"],
            "calendar_span_days": prep_meta["calendar_span_days"],
            "is_contiguous": prep_meta["is_contiguous"],
            "contiguous_dates_count": prep_meta["contiguous_dates_count"],
            "max_contiguous_streak": prep_meta["max_contiguous_streak"],
            "missing_dates_count": prep_meta["missing_dates_count"],
            "has_minimum_dates": prep_meta["has_minimum_dates"],
            "has_seasonal_dates": prep_meta["has_seasonal_dates"],
            "total_records_count": prep_meta["total_records_count"],
            "excluded_records_count": prep_meta["excluded_records_count"],
            "metric_availability": prep_meta["metric_availability"],
        },
        "forecasts": {
            "is_available": forecast_res["is_available"],
            "status": forecast_res["status"],
            "horizon": forecast_res["horizon"],
            "metadata": forecast_res["metadata"],
            "models": forecast_res["models"],
            "revenue_complete": forecast_res["revenue_complete"],
        },
        "validation": {
            "is_available": val_res["is_available"],
            "status": val_res["status"],
            "parameters": val_res["parameters"],
            "metadata": val_res["metadata"],
            "models": val_res["models"],
            "revenue_complete": val_res["revenue_complete"],
        },
        "revenue_complete": revenue_complete,
        "warnings": combined_warnings,
    }
