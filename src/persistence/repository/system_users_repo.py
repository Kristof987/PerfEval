from datetime import datetime


class SystemUsersRepository:
    def find_for_login(self, conn, username: str):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT su.id, su.name, su.username, su.email,
                       sr.name AS role_name, sr.id AS role_id, su.employee_id
                FROM system_users su
                LEFT JOIN system_roles sr ON su.sys_szerep_id = sr.id
                WHERE su.username = %s OR su.name = %s
                """,
                (username, username),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "username": row[2],
                "email": row[3],
                "role_name": row[4],
                "role_id": row[5],
                "employee_id": row[6],
            }

    def update_last_login(self, conn, user_id: int, last_login: datetime) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE system_users
                SET last_login = %s
                WHERE id = %s
                """,
                (last_login, user_id),
            )

    def username_exists(self, conn, username: str) -> bool:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM system_users WHERE username = %s LIMIT 1", (username,))
            return cur.fetchone() is not None

    def email_exists(self, conn, email: str) -> bool:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM system_users WHERE email = %s LIMIT 1", (email,))
            return cur.fetchone() is not None

    def create_system_user(
        self,
        conn,
        name: str,
        username: str,
        email: str,
        system_role_id: int,
        employee_id: int | None,
    ) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO system_users (name, username, email, sys_szerep_id, employee_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, username, email, system_role_id, employee_id),
            )

    def sync_employee_links(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE system_users su
                SET employee_id = oe.id
                FROM organisation_employees oe
                WHERE su.employee_id IS NULL
                  AND (
                    LOWER(su.name) = LOWER(oe.name)
                    OR LOWER(su.username) = LOWER(oe.name)
                  )
                """
            )

    def list_system_users(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT su.id, su.name, su.username, su.email,
                       sr.name AS role_name, sr.id AS role_id,
                       su.created_at, su.employee_id,
                       oe.name AS employee_name
                FROM system_users su
                LEFT JOIN system_roles sr ON su.sys_szerep_id = sr.id
                LEFT JOIN organisation_employees oe ON su.employee_id = oe.id
                ORDER BY su.created_at DESC
                """
            )
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "username": r[2],
                    "email": r[3],
                    "role_name": r[4],
                    "role_id": r[5],
                    "created_at": r[6],
                    "employee_id": r[7],
                    "employee_name": r[8],
                }
                for r in cur.fetchall()
            ]

    def delete_system_user(self, conn, user_id: int) -> int:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM system_users WHERE id = %s", (user_id,))
            return cur.rowcount

