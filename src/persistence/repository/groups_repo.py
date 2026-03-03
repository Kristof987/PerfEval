from dataclasses import dataclass
from typing import Dict, List, Tuple
import psycopg2.extras

@dataclass(frozen=True)
class EmployeeRow:
    id: int
    name: str
    email: str


@dataclass(frozen=True)
class GroupRow:
    id: int
    name: str
    description: str | None
    joined_at: str | None
    member_count: int


class GroupsRepository:
    def get_employee_by_email(self, conn, email: str) -> EmployeeRow | None:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email
                FROM organisation_employees
                WHERE email = %s
                """,
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return EmployeeRow(id=row[0], name=row[1], email=row[2])

    def get_my_groups(self, conn, employee_id: int) -> List[GroupRow]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT g.id, g.name, g.description, eg.joined_at,
                       (SELECT COUNT(*) FROM employee_groups WHERE group_id = g.id) as member_count
                FROM organisation_groups g
                JOIN employee_groups eg ON g.id = eg.group_id
                WHERE eg.employee_id = %s
                ORDER BY g.name
                """,
                (employee_id,),
            )
            rows = cur.fetchall()
            return [
                GroupRow(
                    id=r[0],
                    name=r[1],
                    description=r[2],
                    joined_at=r[3],
                    member_count=int(r[4]),
                )
                for r in rows
            ]

    def get_available_groups(self, conn, employee_id: int) -> List[GroupRow]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT g.id, g.name, g.description,
                       NULL as joined_at,
                       (SELECT COUNT(*) FROM employee_groups WHERE group_id = g.id) as member_count
                FROM organisation_groups g
                WHERE g.id NOT IN (
                    SELECT group_id
                    FROM employee_groups
                    WHERE employee_id = %s
                )
                ORDER BY g.name
                """,
                (employee_id,),
            )
            rows = cur.fetchall()
            return [
                GroupRow(
                    id=r[0],
                    name=r[1],
                    description=r[2],
                    joined_at=None,
                    member_count=int(r[4]),
                )
                for r in rows
            ]

    def get_group_members_for_groups(self, conn, group_ids: List[int], limit_per_group: int | None = None) -> Dict[int, List[Tuple[str, str]]]:
        if not group_ids:
            return {}

        with conn.cursor() as cur:
            if limit_per_group is None:
                cur.execute(
                    """
                    SELECT eg.group_id, e.name, e.email
                    FROM employee_groups eg
                    JOIN organisation_employees e ON e.id = eg.employee_id
                    WHERE eg.group_id = ANY(%s)
                    ORDER BY eg.group_id, e.name
                    """,
                    (group_ids,),
                )
            else:
                cur.execute(
                    """
                    SELECT group_id, name, email
                    FROM (
                        SELECT eg.group_id as group_id,
                               e.name as name,
                               e.email as email,
                               row_number() OVER (PARTITION BY eg.group_id ORDER BY e.name) as rn
                        FROM employee_groups eg
                        JOIN organisation_employees e ON e.id = eg.employee_id
                        WHERE eg.group_id = ANY(%s)
                    ) t
                    WHERE rn <= %s
                    ORDER BY group_id, name
                    """,
                    (group_ids, limit_per_group),
                )

            out: Dict[int, List[Tuple[str, str]]] = {}
            for gid, name, email in cur.fetchall():
                out.setdefault(gid, []).append((name, email))
            return out

    def join_group(self, conn, employee_id: int, group_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO employee_groups (employee_id, group_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (employee_id, group_id),
            )

    def leave_group(self, conn, employee_id: int, group_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM employee_groups
                WHERE employee_id = %s AND group_id = %s
                """,
                (employee_id, group_id),
            )