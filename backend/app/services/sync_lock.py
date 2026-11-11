"""One sync at a time across threads and processes: a PostgreSQL advisory lock (research R9)."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, text

from app.common.constants import SYNC_LOCK_KEY
from app.common.errors import SyncInProgressError

SYNC_IN_PROGRESS_MESSAGE = "A sync is already running. Please wait for it to finish."


@contextmanager
def sync_lock(engine: Engine) -> Iterator[None]:
    """Hold the lock on a dedicated connection for the whole run.

    PostgreSQL also frees the lock if the connection drops.
    """
    with engine.connect() as connection:
        acquired = connection.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": SYNC_LOCK_KEY}
        ).scalar_one()
        if not acquired:
            raise SyncInProgressError(SYNC_IN_PROGRESS_MESSAGE)
        try:
            yield
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": SYNC_LOCK_KEY})
            connection.commit()
