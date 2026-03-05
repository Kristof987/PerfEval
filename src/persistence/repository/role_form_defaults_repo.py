from __future__ import annotations
from typing import Dict, Tuple


class RoleFormDefaultsRepository:
    def get_defaults(self, conn, campaign_id: int) -> Dict[Tuple[str, str], int]:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT evaluator_role, evaluatee_role, form_id
                FROM campaign_role_form_defaults
                WHERE campaign_id = %s
            """, (campaign_id,))
            return {(r[0], r[1]): r[2] for r in cur.fetchall()}

    def upsert_defaults(self, conn, campaign_id: int, role_form_map: Dict[Tuple[str, str], int]) -> None:
        if not role_form_map:
            return
        with conn.cursor() as cur:
            for (evr, eer), form_id in role_form_map.items():
                cur.execute("""
                    INSERT INTO campaign_role_form_defaults
                        (campaign_id, evaluator_role, evaluatee_role, form_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (campaign_id, evaluator_role, evaluatee_role)
                    DO UPDATE SET form_id = EXCLUDED.form_id, updated_at = CURRENT_TIMESTAMP
                """, (campaign_id, evr, eer, form_id))