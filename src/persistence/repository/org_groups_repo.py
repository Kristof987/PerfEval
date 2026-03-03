from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class OrgGroup:
    id: int
    name: str
    description: str | None


class OrgGroupsRepository:
    def create_group(self, conn, name: str, description: str | None) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO organisation_groups (name, description)
                VALUES (%s, %s)
                """,
                (name, description),
            )

    def list_groups(self, conn) -> List[OrgGroup]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, description
                FROM organisation_groups
                ORDER BY name
                """
            )
            return [OrgGroup(id=r[0], name=r[1], description=r[2]) for r in cur.fetchall()]

    def update_group_description(self, conn, group_id: int, description: str | None) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE organisation_groups
                SET description = %s
                WHERE id = %s
                """,
                (description, group_id),
            )

    def delete_group(self, conn, group_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM employee_groups WHERE group_id = %s", (group_id,))
            cur.execute("DELETE FROM organisation_groups WHERE id = %s", (group_id,))

    def list_group_members(self, conn, group_id: int) -> List[Tuple[int, str, str]]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.id, e.name, e.email
                FROM organisation_employees e
                JOIN employee_groups eg ON e.id = eg.employee_id
                WHERE eg.group_id = %s
                ORDER BY e.name
                """,
                (group_id,),
            )
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]

    def remove_member(self, conn, group_id: int, employee_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM employee_groups
                WHERE group_id = %s AND employee_id = %s
                """,
                (group_id, employee_id),
            )

    def add_member(self, conn, group_id: int, employee_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO employee_groups (employee_id, group_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (employee_id, group_id),
            )

    def list_employees_not_in_group(self, conn, group_id: int) -> List[Tuple[int, str, str]]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.id, e.name, e.email
                FROM organisation_employees e
                WHERE e.id NOT IN (
                    SELECT employee_id
                    FROM employee_groups
                    WHERE group_id = %s
                )
                ORDER BY e.name
                """,
                (group_id,),
            )
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]