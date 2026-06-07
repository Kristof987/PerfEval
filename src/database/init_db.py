import os

from sqlalchemy import create_engine, text

from models.base import Base

import models.campaign  # noqa: F401
import models.campaign_group  # noqa: F401
import models.campaign_role_form_default  # noqa: F401
import models.employee  # noqa: F401
import models.employee_group  # noqa: F401
import models.evaluation  # noqa: F401
import models.form  # noqa: F401
import models.organisation_group  # noqa: F401
import models.organisation_role  # noqa: F401
import models.system_permission  # noqa: F401
import models.system_role  # noqa: F401
import models.system_user  # noqa: F401

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://appuser:apppassword@localhost:5432/appdb"
)

BOOTSTRAP_USERNAME = "test_hr_user"
BOOTSTRAP_EMAIL = "test_hr_user@example.com"
BOOTSTRAP_ROLE = "HR employee"


def seed_first_system_user(engine) -> bool:
    """Create the initial HR user only when the system has no users yet."""
    with engine.begin() as conn:
        user_count = conn.execute(text("SELECT COUNT(*) FROM system_users")).scalar_one()
        if user_count > 0:
            return False

        role_id = conn.execute(
            text(
                """
                INSERT INTO system_roles (name)
                VALUES (:name)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """
            ),
            {"name": BOOTSTRAP_ROLE},
        ).scalar_one()

        conn.execute(
            text(
                """
                INSERT INTO system_users (name, username, email, sys_szerep_id, created_at)
                VALUES (:name, :username, :email, :role_id, NOW())
                """
            ),
            {
                "name": BOOTSTRAP_USERNAME,
                "username": BOOTSTRAP_USERNAME,
                "email": BOOTSTRAP_EMAIL,
                "role_id": role_id,
            },
        )
        return True


def init_db() -> None:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    seed_first_system_user(engine)


if __name__ == "__main__":
    init_db()
    print("Database initialised successfully.")
