from __future__ import annotations
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, insert
from sqlalchemy.orm import Session

from models.campaign import Campaign

class CampaignRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_campaigns(self) -> List[Campaign]:
        query = select(Campaign).order_by(Campaign.start_date.desc())
        return self.session.scalars(query).all()

    def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        return self.session.get(Campaign, campaign_id)

    def create_campaign(self, name: str, description: str, start_date: datetime,
                        end_date: Optional[datetime], comment: Optional[str]) -> int:

        campaign = Campaign(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            comment=comment,
        )

        self.session.add(campaign)
        self.session.flush()
        return int(campaign.id)

    def update_campaign(self, conn, campaign_id: int, name: str, description: str,
                        start_date: datetime, end_date: Optional[datetime],
                        is_active: bool, comment: Optional[str]) -> None:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE campaign
                SET name=%s, description=%s, start_date=%s, end_date=%s, is_active=%s, comment=%s
                WHERE id=%s
            """, (name, description, start_date, end_date, is_active, comment, campaign_id))

    def delete_campaign(self, conn, campaign_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM evaluation WHERE campaign_id=%s", (campaign_id,))
            cur.execute("DELETE FROM campaign WHERE id=%s", (campaign_id,))

    def toggle_active(self, conn, campaign_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute("UPDATE campaign SET is_active = NOT is_active WHERE id=%s", (campaign_id,))
