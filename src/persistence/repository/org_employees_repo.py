from dataclasses import dataclass
from typing import List, Tuple

@dataclass(frozen=True)
class OrgEmployee:
    id: int
    name: str
    email: str
    role: str | None


class OrgEmployeesRepository:
    def employee_exists_by_id(self, conn, employee_id: int) -> bool:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM organisation_employees
                WHERE id = %s
                LIMIT 1
                """,
                (employee_id,),
            )
            return cur.fetchone() is not None

    def employee_exists_by_name_ci(self, conn, name: str) -> bool:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM organisation_employees
                WHERE LOWER(name) = LOWER(%s)
                LIMIT 1
                """,
                (name,),
            )
            return cur.fetchone() is not None

    def create_employee(self, conn, name: str, email: str, org_role_name: str | None) -> int:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO organisation_employees (name, email, org_role_name)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (name, email, org_role_name),
            )
            return cur.fetchone()[0]

    def create_system_user_for_employee(
        self,
        conn,
        name: str,
        username: str,
        email: str,
        sys_role_id: int,
        employee_id: int,
    ) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO system_users (name, username, email, sys_szerep_id, employee_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, username, email, sys_role_id, employee_id),
            )

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
