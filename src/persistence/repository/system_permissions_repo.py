class SystemPermissionsRepository:
    def list_permissions(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, description
                FROM system_permissions
                ORDER BY name
                """
            )
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "description": r[2],
                }
                for r in cur.fetchall()
            ]

    def create_permission(self, conn, name: str, description: str) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO system_permissions (name, description)
                VALUES (%s, %s)
                """,
                (name, description),
            )

