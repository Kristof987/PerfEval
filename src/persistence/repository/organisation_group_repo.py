# app/persistence/repositories/organisation_group_repo.py
from __future__ import annotations
from typing import List, Dict

class OrganisationGroupRepository:
    def list_groups(self, conn) -> List[Dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT id, uuid, name, description FROM organisation_groups ORDER BY name")
            return [{"id": r[0], "uuid": r[1], "name": r[2], "description": r[3]} for r in cur.fetchall()]

    def list_campaign_groups(self, conn, campaign_id: int) -> List[Dict]:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT g.id, g.uuid, g.name, g.description
                FROM organisation_groups g
                JOIN campaign_groups cg ON g.id = cg.group_id
                WHERE cg.campaign_id = %s
                ORDER BY g.name
            """, (campaign_id,))
            return [{"id": r[0], "uuid": r[1], "name": r[2], "description": r[3]} for r in cur.fetchall()]

    def assign_to_campaign(self, conn, campaign_id: int, group_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO campaign_groups (campaign_id, group_id)
                VALUES (%s, %s)
                ON CONFLICT (campaign_id, group_id) DO NOTHING
            """, (campaign_id, group_id))

    def remove_from_campaign(self, conn, campaign_id: int, group_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM campaign_groups WHERE campaign_id=%s AND group_id=%s", (campaign_id, group_id))

    def list_group_members(self, conn, group_id: int) -> List[Dict]:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, e.uuid, e.name, e.email
                FROM organisation_employees e
                JOIN employee_groups eg ON e.id = eg.employee_id
                WHERE eg.group_id = %s
                ORDER BY e.name
            """, (group_id,))
            return [{"id": r[0], "uuid": r[1], "name": r[2], "email": r[3]} for r in cur.fetchall()]