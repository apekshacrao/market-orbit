"""
Walk-forward temporal validation for Market Orbit baseline forecasting models.

Evaluates deterministic baseline models (naive persistence, 7-day simple moving
average, and 7-day seasonal naive) using expanding-window temporal splits, strictly
preventing future lookahead leakage and respecting historical data completeness.
"""

import datetime
import math
from typing import Dict, Any, List, Optional
import pandas as pd

from analytics.trends.customer_trends import _parse_valid_date
from analytics.forecasting.data_prep import (
    prepare_daily_series,
    SUPPORTED_METRICS,
    _validate_positive_int,
)
from analytics.forecasting.baselines import forecast_baselines

MODEL_NAMES = {
    "naive": "naive_persistence",
    "sma_7": "simple_moving_average_7d",
    "seasonal_naive": "seasonal_naive_7d",
}


def validate_baselines(
    df: pd.DataFrame,
    horizon: int = 7,
    min_train_dates: int = 14,
    step: int = 1,
) -> Dict[str, Any]:
    """
    Executes a leakage-safe walk-forward validation across deterministic baseline models.

    Uses expanding-window temporal splits where each forecast origin uses exclusively
    observations dated on or before that origin. Forecasts are generated for the next
    `horizon` calendar days and compared only against valid observed actuals on the
    exact same calendar dates.

    Args:
        df: Pandas DataFrame containing historical marketing records with 'date' and
            optional additive metrics (spend, conversions, clicks, impressions, revenue).
        horizon: Positive integer number of calendar days to project ahead (default 7).
        min_train_dates: Positive integer minimum number of distinct historical dates
            required for the initial training split (default 14).
        step: Positive integer number of observed calendar dates to advance the
            forecast origin between splits (default 1).

    Returns:
        Dict with:
        - 'is_available': bool indicating whether walk-forward validation executed.
        - 'status': str diagnostic status ('ready', 'insufficient_history', or 'unavailable').
        - 'parameters': dict of validation parameters (horizon, min_train_dates, step).
        - 'metadata': dict with dataset date coverage, total origins, and origin details.
        - 'models': dict per model with eligibility counts, error metrics, and sample sizes.
        - 'revenue_complete': bool indicating if revenue tracking was complete across all dates.
        - 'warnings': list of diagnostic warnings.

    Raises:
        ValueError: If horizon, min_train_dates, or step is not a positive integer.
    """
    # 1. Parameter Validation
    horizon = _validate_positive_int(horizon, "Forecast horizon")
    min_train_dates = _validate_positive_int(min_train_dates, "min_train_dates")
    step = _validate_positive_int(step, "step")

    empty_models = {
        key: {
            "model_name": name,
            "origins_eligible": 0,
            "origins_ineligible": 0,
            "ineligibility_reasons": [],
            "metrics": {
                m: {
                    "points_evaluated": 0,
                    "mae": None,
                    "rmse": None,
                    "wape": None,
                    "wape_status": "no_evaluated_points",
                }
                for m in SUPPORTED_METRICS
            },
        }
        for key, name in MODEL_NAMES.items()
    }

    empty_result: Dict[str, Any] = {
        "is_available": False,
        "status": "unavailable",
        "parameters": {
            "horizon": horizon,
            "min_train_dates": min_train_dates,
            "step": step,
        },
        "metadata": {
            "dataset_start_date": None,
            "dataset_end_date": None,
            "total_valid_dates": 0,
            "total_origins_generated": 0,
            "aggregation_method": "point_weighted_pooled",
            "origins": [],
        },
        "models": empty_models,
        "revenue_complete": False,
        "warnings": [],
    }

    if df is None or df.empty or "date" not in df.columns:
        empty_result["warnings"].append("Dataset is empty or missing mandatory 'date' column.")
        return empty_result

    # 2. Strict Date Parsing & Chronological Ordering
    parsed_dates = df["date"].apply(_parse_valid_date)
    valid_mask = parsed_dates.notna()
    if int(valid_mask.sum()) == 0:
        empty_result["status"] = "no_valid_dates"
        empty_result["warnings"].append("No valid calendar dates (YYYY-MM-DD) found in dataset.")
        return empty_result

    # 3. Ground Truth Daily Series Preparation across Entire Timeline
    full_prep = prepare_daily_series(df)
    if not full_prep["is_available"]:
        empty_result["status"] = full_prep["status"]
        empty_result["warnings"].extend(full_prep["warnings"])
        return empty_result

    full_series = full_prep["series"]
    full_meta = full_prep["metadata"]
    total_valid_dates = full_meta["historical_dates_count"]
    revenue_complete = full_prep["revenue_complete"]

    # Map actual observations by calendar date string for O(1) alignment
    actuals_by_date = {row["date"]: row for row in full_series}
    distinct_date_objs: List[datetime.date] = [
        datetime.datetime.strptime(row["date"], "%Y-%m-%d").date()
        for row in full_series
    ]

    # Require at least (min_train_dates + 1) distinct dates to evaluate at least 1 test observation
    if total_valid_dates <= min_train_dates:
        empty_result["status"] = "insufficient_history"
        empty_result["metadata"]["dataset_start_date"] = full_meta["start_date"]
        empty_result["metadata"]["dataset_end_date"] = full_meta["end_date"]
        empty_result["metadata"]["total_valid_dates"] = total_valid_dates
        empty_result["revenue_complete"] = revenue_complete
        empty_result["warnings"].append(
            f"Dataset contains {total_valid_dates} distinct date(s); at least {min_train_dates + 1} "
            f"distinct dates are required for walk-forward validation with min_train_dates={min_train_dates}."
        )
        return empty_result

    # 4. Walk-Forward Expanding-Window Temporal Evaluation
    # Start at origin index k where training dates count == min_train_dates (k = min_train_dates - 1)
    # Stop when k reaches the last date in the dataset (k < total_valid_dates - 1)
    origin_indices: List[int] = []
    curr_k = min_train_dates - 1
    while curr_k < total_valid_dates - 1:
        origin_indices.append(curr_k)
        curr_k += step

    warnings: List[str] = list(full_prep["warnings"])
    if not revenue_complete:
        warnings.append(
            "Historical revenue is incomplete or untracked across the dataset; revenue forecasting "
            "and evaluation are restricted to null."
        )

    # Accumulators for point-weighted pooled error metrics across all eligible origins:
    # {model_key: {metric: {"sum_abs_err": float, "sum_sq_err": float, "sum_actual": float, "count": int}}}
    error_accumulators = {
        model_key: {
            m: {"sum_abs_err": 0.0, "sum_sq_err": 0.0, "sum_actual": 0.0, "count": 0}
            for m in SUPPORTED_METRICS
        }
        for model_key in MODEL_NAMES
    }

    origins_eligible_counts = {k: 0 for k in MODEL_NAMES}
    origins_ineligible_counts = {k: 0 for k in MODEL_NAMES}
    ineligibility_reasons_map = {k: set() for k in MODEL_NAMES}

    origin_summaries: List[Dict[str, Any]] = []

    for orig_idx, k in enumerate(origin_indices):
        origin_date_obj = distinct_date_objs[k]
        origin_date_str = origin_date_obj.strftime("%Y-%m-%d")

        # Zero-leakage slice: strictly include records dated on or before this origin
        train_mask = valid_mask & (parsed_dates <= origin_date_obj)
        train_df = df[train_mask].copy()

        # Generate baseline forecast from the training slice
        baseline_res = forecast_baselines(train_df, horizon=horizon)
        train_meta = baseline_res["metadata"]
        train_dates_count = train_meta["historical_dates_count"]
        train_start_str = train_meta["start_date"]
        train_end_str = train_meta["end_date"]
        f_start_str = train_meta["forecast_start_date"]
        f_end_str = train_meta["forecast_end_date"]
        train_rev_complete = baseline_res["revenue_complete"]

        origin_models_summary: Dict[str, Any] = {}

        # Expected forecast dates for this origin: (origin_date_obj + 1 day) to (origin_date_obj + horizon days)
        expected_f_dates = [
            (origin_date_obj + datetime.timedelta(days=d)).strftime("%Y-%m-%d")
            for d in range(1, horizon + 1)
        ]
        observed_eval_dates = [d for d in expected_f_dates if d in actuals_by_date]

        for model_key in MODEL_NAMES:
            model_out = baseline_res["models"][model_key]
            is_eligible = model_out["is_eligible"]
            ineligibility_reason = model_out["ineligibility_reason"]

            points_evaluated_per_metric = {m: 0 for m in SUPPORTED_METRICS}

            if not is_eligible:
                origins_ineligible_counts[model_key] += 1
                if ineligibility_reason:
                    ineligibility_reasons_map[model_key].add(ineligibility_reason)
            else:
                origins_eligible_counts[model_key] += 1
                forecast_list = model_out["forecast"]

                for pt in forecast_list:
                    fc_date = pt["date"]
                    # Strictly evaluate against actual observation on the identical calendar date
                    if fc_date not in actuals_by_date:
                        continue

                    actual_pt = actuals_by_date[fc_date]

                    for m in SUPPORTED_METRICS:
                        pred_val = pt[m]
                        act_val = actual_pt[m]

                        # Revenue evaluation guard: training split must have complete revenue AND actual must be present
                        if m == "revenue" and not train_rev_complete:
                            continue

                        # Compare forecasts with actuals only where both forecast and actual are validly observed
                        if pred_val is not None and act_val is not None:
                            err = float(pred_val) - float(act_val)
                            abs_err = abs(err)
                            sq_err = err ** 2

                            acc = error_accumulators[model_key][m]
                            acc["sum_abs_err"] += abs_err
                            acc["sum_sq_err"] += sq_err
                            acc["sum_actual"] += abs(float(act_val))
                            acc["count"] += 1
                            points_evaluated_per_metric[m] += 1

            origin_models_summary[model_key] = {
                "is_eligible": is_eligible,
                "ineligibility_reason": ineligibility_reason,
                "points_evaluated": points_evaluated_per_metric,
            }

        origin_summaries.append({
            "origin_index": orig_idx,
            "origin_date": origin_date_str,
            "train_dates_count": train_dates_count,
            "train_start_date": train_start_str,
            "train_end_date": train_end_str,
            "forecast_start_date": f_start_str,
            "forecast_end_date": f_end_str,
            "observed_eval_dates_count": len(observed_eval_dates),
            "models": origin_models_summary,
        })

    # 5. Aggregate Metric Calculation (Point-Weighted Pooled Method)
    # Aggregated scores are computed directly from the pooled underlying errors
    # rather than taking an unweighted average of per-origin scores with unequal sample sizes.
    evaluated_models: Dict[str, Any] = {}

    for model_key, model_name in MODEL_NAMES.items():
        metrics_eval: Dict[str, Any] = {}

        for m in SUPPORTED_METRICS:
            acc = error_accumulators[model_key][m]
            count = acc["count"]

            if count == 0:
                mae = None
                rmse = None
                wape = None
                wape_status = "no_evaluated_points"
            else:
                mae = round(acc["sum_abs_err"] / count, 4)
                rmse = round(math.sqrt(acc["sum_sq_err"] / count), 4)

                # WAPE denominator zero guard: if sum of actuals is zero, WAPE is undefined
                if acc["sum_actual"] == 0.0:
                    wape = None
                    wape_status = "undefined_zero_actuals"
                else:
                    wape = round((acc["sum_abs_err"] / acc["sum_actual"]) * 100.0, 4)
                    wape_status = "available"

            metrics_eval[m] = {
                "points_evaluated": count,
                "mae": mae,
                "rmse": rmse,
                "wape": wape,
                "wape_status": wape_status,
            }

        evaluated_models[model_key] = {
            "model_name": model_name,
            "origins_eligible": origins_eligible_counts[model_key],
            "origins_ineligible": origins_ineligible_counts[model_key],
            "ineligibility_reasons": sorted(list(ineligibility_reasons_map[model_key])),
            "metrics": metrics_eval,
        }

    return {
        "is_available": True,
        "status": "ready",
        "parameters": {
            "horizon": horizon,
            "min_train_dates": min_train_dates,
            "step": step,
        },
        "metadata": {
            "dataset_start_date": full_meta["start_date"],
            "dataset_end_date": full_meta["end_date"],
            "total_valid_dates": total_valid_dates,
            "total_origins_generated": len(origin_indices),
            "aggregation_method": "point_weighted_pooled",
            "origins": origin_summaries,
        },
        "models": evaluated_models,
        "revenue_complete": revenue_complete,
        "warnings": warnings,
    }
