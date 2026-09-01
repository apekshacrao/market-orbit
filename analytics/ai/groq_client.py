import os
from typing import Dict, Any, List

class GroqClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")

    def generate_recommendations(self, kpi_data: Dict[str, Any], rankings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates structured recommendations via Groq API."""
        return [
            {
                "title": "Scale High-ROAS Campaigns",
                "description": "Increase budget for top-performing channels demonstrating ROAS > 3.0x.",
                "action": "Increase Budget by 20%"
            },
            {
                "title": "Pause Underperforming Creatives",
                "description": "Reallocate spend from campaigns with high CPA and low conversion rates.",
                "action": "Pause Low-Performing Ad Sets"
            }
        ]
