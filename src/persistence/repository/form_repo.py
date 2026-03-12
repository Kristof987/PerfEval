from __future__ import annotations
from typing import List, Dict

class FormRepository:
    def list_forms(self, conn) -> List[Dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT id, uuid, name, description FROM form ORDER BY name")
            return [{"id": r[0], "uuid": r[1], "name": r[2], "description": r[3]} for r in cur.fetchall()]