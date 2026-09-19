import csv
from datetime import datetime
from decimal import Decimal, DecimalException
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.campaign import Campaign
from app.db.models.dataset import Dataset


class CampaignService:

    @staticmethod
    def import_campaigns(
        file_path: str,
        dataset_id: str,
        db: Session,
    ):
        campaigns = []

        try:
            with open(
                file_path,
                newline="",
                encoding="utf-8",
            ) as file:
                reader = csv.DictReader(file)

                for row_number, row in enumerate(reader, start=2):
                    try:
                        campaign = Campaign(
                            id=str(uuid4()),
                            dataset_id=dataset_id,

                            campaign_name=row["campaign_name"].strip(),
                            channel=row["channel"].strip(),

                            impressions=int(
                                row.get("impressions") or 0
                            ),
                            clicks=int(
                                row.get("clicks") or 0
                            ),

                            spend=Decimal(
                                (row["spend"] or "0").strip() or "0"
                            ),

                            conversions=int(
                                row.get("conversions") or 0
                            ),

                            # Revenue is optional
                            revenue=(
                                Decimal(row["revenue"].strip())
                                if row.get("revenue")
                                and row["revenue"].strip()
                                else None
                            ),

                            # Optional date field
                            date=(
                                datetime.strptime(
                                    row["date"].strip(),
                                    "%Y-%m-%d",
                                ).date()
                                if row.get("date")
                                and row["date"].strip()
                                else None
                            ),

                            # Optional demographic fields
                            location=(
                                row["location"].strip()
                                if row.get("location")
                                and row["location"].strip()
                                else None
                            ),

                            age_group=(
                                row["age_group"].strip()
                                if row.get("age_group")
                                and row["age_group"].strip()
                                else None
                            ),

                            customer_segment=(
                                row["customer_segment"].strip()
                                if row.get("customer_segment")
                                and row["customer_segment"].strip()
                                else None
                            ),

                            device=(
                                row["device"].strip()
                                if row.get("device")
                                and row["device"].strip()
                                else None
                            ),
                        )

                        campaigns.append(campaign)

                    except (ValueError, KeyError, DecimalException) as exc:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=(
                                f"Invalid data in CSV row "
                                f"{row_number}: {exc}"
                            ),
                        )

        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset file not found",
            )

        if not campaigns:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CSV file contains no campaign data",
            )

        db.add_all(campaigns)

        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if dataset:
            dataset.row_count = len(campaigns)

        return campaigns