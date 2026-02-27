from contextlib import contextmanager
from dataclasses import dataclass
import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool


@dataclass(frozen=True)
class DbConfig:
    dsn: str


class Database:
    def __init__(self, config: DbConfig, minconn: int = 1, maxconn: int = 5):
        self._pool = SimpleConnectionPool(minconn, maxconn, dsn=config.dsn)

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


# simple singleton factory (ha nem akarsz DI frameworköt)
_db: Database | None = None

def get_db() -> Database:
    global _db
    if _db is None:
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            raise RuntimeError("DATABASE_URL is not set")
        _db = Database(DbConfig(dsn=dsn))
    return _db