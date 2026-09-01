RECOMMENDATION_PROMPT_TEMPLATE = """
You are an expert marketing data scientist. Analyze the following marketing campaign metrics:

KPI Summary:
{kpi_summary}

Top Campaigns:
{top_campaigns}

Underperforming Campaigns:
{bottom_campaigns}

Provide actionable, high-impact recommendations to improve overall ROAS and reduce wasted spend.
"""
