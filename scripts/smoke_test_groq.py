"""
Controlled Live Groq Smoke Test Script for Market Orbit.

Explicitly invoked verification tool to test real Groq API connectivity,
prompt engineering, live inference, and structured response parsing.

Usage:
    python scripts/smoke_test_groq.py

Requirements:
- Reads GROQ_API_KEY from project root .env or environment.
- Never prints or exposes the API key.
- Does NOT execute automatically during pytest.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.ai.groq_client import load_groq_config, GroqClient
from analytics.ai.pipeline import (
    run_recommendation_pipeline,
    PipelineConfigurationError,
    PipelineAuthenticationError,
    PipelineProviderError,
    PipelineParsingError,
    PipelineValidationError,
)


def run_smoke_test() -> int:
    print("=" * 70)
    print("Market Orbit — Controlled Live Groq Inference Smoke Test")
    print("=" * 70)

    # 1. Resolve configuration
    config = load_groq_config()
    api_key = config.get("api_key", "")
    model = config.get("model", "")
    timeout = config.get("timeout", 15.0)

    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Configured Model: {model}")
    print(f"Timeout: {timeout}s")

    if not api_key:
        print("\n[ERROR] GROQ_API_KEY is NOT configured.")
        print("Please set GROQ_API_KEY in market-orbit/.env or export it in your environment.")
        return 1

    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    print(f"API Key Status: Configured ({masked_key})")
    print("\nExecuting live request with minimal test context...")

    # 2. Minimal test context
    kpi_summary = {
        "total_spend": 1250.0,
        "total_revenue": 4500.0,
        "total_impressions": 50000,
        "total_clicks": 1800,
        "total_conversions": 95,
        "roas": 3.6,
        "cpa": 13.16,
        "cpc": 0.69,
        "ctr_percent": 3.6,
        "conversion_rate_percent": 5.28,
        "revenue_tracked": True,
    }
    campaign_rankings = {
        "top": [
            {
                "campaign_name": "Summer_Search_Alpha",
                "spend": 500.0,
                "revenue": 2400.0,
                "roas": 4.8,
                "conversions": 50,
            }
        ],
        "bottom": [
            {
                "campaign_name": "Display_Cold_Beta",
                "spend": 300.0,
                "revenue": 210.0,
                "roas": 0.7,
                "conversions": 5,
            }
        ],
    }

    try:
        client = GroqClient(api_key=api_key, model=model, timeout=timeout)
        batch = run_recommendation_pipeline(
            kpi_summary=kpi_summary,
            campaign_rankings=campaign_rankings,
            client=client,
            model=model,
            dataset_id="smoke-test-dataset-001",
        )

        print("\n[SUCCESS] Live Groq API response received and successfully validated!")
        print(f"Total Recommendations Generated: {len(batch.recommendations)}")
        print("-" * 70)

        for idx, rec in enumerate(batch.recommendations, 1):
            print(f"[{idx}] ID: {rec.id} | Category: {rec.category.value} | Source: {rec.source.value}")
            print(f"    Title: {rec.title}")
            print(f"    Action: {rec.action}")
            print(f"    Rationale: {rec.rationale[:120]}...")
            if rec.supporting_evidence:
                ev = rec.supporting_evidence
                print(f"    Evidence: {ev.metric}={ev.observed_value} ({ev.campaign_name or 'account'})")
            print()

        print("=" * 70)
        print("Smoke Test Verdict: PASS (Live inference & parsing verified)")
        print("=" * 70)
        return 0

    except PipelineConfigurationError as exc:
        print(f"\n[CONFIG ERROR] {exc}")
        return 1
    except PipelineAuthenticationError as exc:
        print(f"\n[AUTH ERROR] Groq API rejected credentials (401/403): {exc}")
        return 2
    except PipelineProviderError as exc:
        print(f"\n[PROVIDER ERROR] Groq API returned error: {exc}")
        return 3
    except (PipelineParsingError, PipelineValidationError) as exc:
        print(f"\n[PARSING/VALIDATION ERROR] Live LLM response failed schema validation: {exc}")
        return 4
    except Exception as exc:
        print(f"\n[UNEXPECTED ERROR] {exc}")
        return 5


if __name__ == "__main__":
    sys.exit(run_smoke_test())
