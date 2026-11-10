"""TestClient wired to the rolled-back test database and the fake PayPal and FX gateways."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_fx_gateway, get_gateway
from app.db import get_engine, get_session, get_session_factory
from app.fakes.fx_fake import FakeFxGateway
from app.fakes.paypal_fake import FakePayPalGateway
from app.main import create_app


@pytest.fixture
def fake_gateway() -> FakePayPalGateway:
    return FakePayPalGateway()


@pytest.fixture
def fake_fx() -> FakeFxGateway:
    return FakeFxGateway()


@pytest.fixture
def api(
    session_factory: sessionmaker[Session],
    db_engine: Engine,
    fake_gateway: FakePayPalGateway,
    fake_fx: FakeFxGateway,
) -> Iterator[TestClient]:
    app = create_app()

    def session_dependency() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_session] = session_dependency
    app.dependency_overrides[get_engine] = lambda: db_engine
    app.dependency_overrides[get_gateway] = lambda: fake_gateway
    app.dependency_overrides[get_fx_gateway] = lambda: fake_fx
    yield TestClient(app)
