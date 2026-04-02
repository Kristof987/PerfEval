from contextlib import contextmanager
from dataclasses import dataclass
import os
from psycopg2.pool import SimpleConnectionPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import all ORM models so SQLAlchemy mapper relationships are fully configured
# before any session.query() is called.
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


@dataclass(frozen=True)
class DbConfig:
    dsn: str


class Database:
    def __init__(self, config: DbConfig, minconn: int = 1, maxconn: int = 5):
        self._pool = SimpleConnectionPool(minconn, maxconn, dsn=config.dsn)
        # SQLAlchemy engine for ORM-based repositories
        # DATABASE_URL uses postgresql+psycopg2:// scheme for SQLAlchemy
        sa_url = config.dsn if config.dsn.startswith("postgresql") else f"postgresql+psycopg2://{config.dsn}"
        self._engine = create_engine(sa_url)
        self._Session = sessionmaker(bind=self._engine)

    @contextmanager
    def connection(self):
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    @contextmanager
    def transaction(self):
        with self.connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    @contextmanager
    def session(self):
        """Yield a SQLAlchemy ORM Session (auto-commit on success, rollback on error)."""
        sess: Session = self._Session()
        try:
            yield sess
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        finally:
            sess.close()


_db: Database | None = None

def get_db() -> Database:
    global _db
    if _db is None:
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            raise RuntimeError("DATABASE_URL is not set")
        _db = Database(DbConfig(dsn=dsn))
    return _db