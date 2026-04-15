from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class SystemRole:
    id: int
    name: str


class SystemRolesRepository:
    def list_roles(self, conn) -> List[SystemRole]:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM system_roles ORDER BY name")
            return [SystemRole(id=r[0], name=r[1]) for r in cur.fetchall()]

    def list_roles_with_permissions(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sr.id, sr.name, sp.name AS permission_name
                FROM system_roles sr
                LEFT JOIN system_permissions sp ON sr.system_permission_id = sp.id
                ORDER BY sr.name
                """
            )
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "permission_name": r[2],
                }
                for r in cur.fetchall()
            ]

    def create_role(self, conn, name: str, permission_id: int | None) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO system_roles (name, system_permission_id)
                VALUES (%s, %s)
                """,
                (name, permission_id),
            )
