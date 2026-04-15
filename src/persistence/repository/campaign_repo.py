from __future__ import annotations
from datetime import datetime
from typing import Optional, List

from models.campaign import Campaign

class CampaignRepository:
    def __init__(self):
        pass

    def list_campaigns(self, session) -> List[Campaign]:
        return session.query(Campaign).order_by(Campaign.start_date.desc()).all()

    def get_campaign(self, session, campaign_id: int) -> Optional[Campaign]:
        return session.query(Campaign).filter(Campaign.id == campaign_id).first()

    def create_campaign(self, conn, name: str, description: str, start_date: datetime,
                        end_date: Optional[datetime], comment: Optional[str]) -> int:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO campaign (name, description, start_date, end_date, is_active, comment)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (name, description, start_date, end_date, True, comment),
            )
            row = cur.fetchone()
            return int(row[0])

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
