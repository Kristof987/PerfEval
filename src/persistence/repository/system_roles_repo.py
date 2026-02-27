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