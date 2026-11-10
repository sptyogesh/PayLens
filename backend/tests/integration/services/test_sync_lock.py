import pytest
from sqlalchemy import Engine

from app.common.errors import SyncInProgressError
from app.services.sync_lock import sync_lock


def test_second_acquire_is_refused_until_release(db_engine: Engine) -> None:
    with sync_lock(db_engine), pytest.raises(SyncInProgressError), sync_lock(db_engine):
        pass
    with sync_lock(db_engine):
        pass
