from dataclasses import dataclass
from typing import List, Tuple

@dataclass(frozen=True)
class OrgEmployee:
    id: int
    name: str
    email: str
    role: str | None


class OrgEmployeesRepository:
    def list_employees(self, conn) -> List[OrgEmployee]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email, org_role_name
                FROM organisation_employees
                ORDER BY name
                """
            )
            return [OrgEmployee(id=r[0], name=r[1], email=r[2], role=r[3]) for r in cur.fetchall()]

    def list_employee_groups(self, conn, employee_id: int) -> List[Tuple[int, str]]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT g.id, g.name
                FROM organisation_groups g
                JOIN employee_groups eg ON g.id = eg.group_id
                WHERE eg.employee_id = %s
                ORDER BY g.name
                """,
                (employee_id,),
            )
            return [(r[0], r[1]) for r in cur.fetchall()]

    def list_groups_employee_not_in(self, conn, employee_id: int) -> List[Tuple[int, str]]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT g.id, g.name
                FROM organisation_groups g
                WHERE g.id NOT IN (
                    SELECT group_id FROM employee_groups WHERE employee_id = %s
                )
                ORDER BY g.name
                """,
                (employee_id,),
            )
            return [(r[0], r[1]) for r in cur.fetchall()]

    def remove_employee_from_group(self, conn, employee_id: int, group_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM employee_groups
                WHERE employee_id = %s AND group_id = %s
                """,
                (employee_id, group_id),
            )