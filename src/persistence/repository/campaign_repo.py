from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass(frozen=True)
class CampaignRow:
    id: int
    uuid: str
    name: str
    description: str
    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool
    comment: Optional[str]
    completed: int
    total: int


class CampaignRepository:
    def list_campaigns(self, conn) -> List[CampaignRow]:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    c.id, c.uuid, c.name, c.description, c.start_date, c.end_date,
                    c.is_active, c.comment,
                    COUNT(e.id) FILTER (WHERE e.status = 'completed') as completed_count,
                    COUNT(e.id) as total_count
                FROM campaign c
                LEFT JOIN evaluation e ON c.id = e.campaign_id
                GROUP BY c.id, c.uuid, c.name, c.description, c.start_date, c.end_date, c.is_active, c.comment
                ORDER BY c.start_date DESC
            """)
            return [
                CampaignRow(
                    id=r[0], uuid=r[1], name=r[2], description=r[3],
                    start_date=r[4], end_date=r[5], is_active=r[6],
                    comment=r[7], completed=r[8] or 0, total=r[9] or 0
                )
                for r in cur.fetchall()
            ]

    def get_campaign(self, conn, campaign_id: int) -> Optional[CampaignRow]:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    c.id, c.uuid, c.name, c.description, c.start_date, c.end_date,
                    c.is_active, c.comment,
                    COUNT(e.id) FILTER (WHERE e.status = 'completed') as completed_count,
                    COUNT(e.id) as total_count
                FROM campaign c
                LEFT JOIN evaluation e ON c.id = e.campaign_id
                WHERE c.id = %s
                GROUP BY c.id, c.uuid, c.name, c.description, c.start_date, c.end_date, c.is_active, c.comment
            """, (campaign_id,))
            r = cur.fetchone()
            if not r:
                return None
            return CampaignRow(
                id=r[0], uuid=r[1], name=r[2], description=r[3],
                start_date=r[4], end_date=r[5], is_active=r[6],
                comment=r[7], completed=r[8] or 0, total=r[9] or 0
            )

    def create_campaign(self, conn, name: str, description: str, start_date: datetime,
                        end_date: Optional[datetime], comment: Optional[str]) -> int:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO campaign (name, description, start_date, end_date, is_active, comment)
                VALUES (%s, %s, %s, %s, TRUE, %s)
                RETURNING id
            """, (name, description, start_date, end_date, comment))
            return int(cur.fetchone()[0])

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