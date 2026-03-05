# app/persistence/repositories/organisation_role_repo.py
from __future__ import annotations
from typing import List, Dict

class OrganisationRoleRepository:
    def list_roles(self, conn) -> List[Dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM organisation_roles ORDER BY name")
            return [{"id": r[0], "name": r[1], "description": r[2]} for r in cur.fetchall()]