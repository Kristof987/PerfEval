# app/persistence/repositories/employee_repo.py
from __future__ import annotations
from typing import Dict, List, Optional

class EmployeeRepository:
    def get_roles_map(self, conn, employee_ids: List[int]) -> Dict[int, Optional[str]]:
        if not employee_ids:
            return {}
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, COALESCE(r.name, e.org_role_name) as role_name
                FROM organisation_employees e
                LEFT JOIN organisation_roles r ON e.org_role_id = r.id
                WHERE e.id = ANY(%s)
            """, (employee_ids,))
            return {r[0]: r[1] for r in cur.fetchall()}