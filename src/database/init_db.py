import os

from sqlalchemy import create_engine

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

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://appuser:apppassword@localhost:5432/appdb"
)

def init_db() -> None:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("Database initialised successfully.")
