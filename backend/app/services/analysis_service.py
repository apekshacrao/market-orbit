class AnalysisService:
    @staticmethod
    def get_results(dataset_id: str):
        return {
            "dataset_id": dataset_id,
            "kpis": {"total_spend": 10000, "total_revenue": 35000, "overall_roas": 3.5},
            "rankings": {"top": [], "bottom": []},
            "trends": {},
            "ai_recommendations": []
        }

    @staticmethod
    def get_kpis(dataset_id: str):
        return {
            "total_spend": 10000.0,
            "total_revenue": 35000.0,
            "overall_roas": 3.5,
            "avg_conversion_rate": 0.045,
            "avg_cpa": 22.50
        }
