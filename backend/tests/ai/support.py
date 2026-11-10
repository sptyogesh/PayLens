"""Seed data and helpers shared by the golden and safety chat tests."""

from datetime import UTC, datetime

from freezegun import freeze_time
from sqlalchemy.orm import Session

from app.ai.agent import answer_question
from app.fakes.fx_fake import FakeFxGateway
from app.fakes.llm_fake import FakeLlm
from app.schemas.chat import ChatIn, ChatOut
from app.services.leakage_service import recalculate_leakage
from tests.fixtures.rows import add_client, add_tx

NOW = datetime(2026, 11, 10, 6, 0, tzinfo=UTC)
# (tx id, client index, month, day, gross, fee): FY 2025-26 and 2026-27, three currencies.
PAYMENTS = (
    ("FEB", 0, 2, 10, "800.00", "35.50"),
    ("APR", 1, 4, 14, "450.00", "20.10"),
    ("MAY", 2, 5, 20, "1200.00", "52.30"),
    ("JUL", 0, 7, 3, "1500.00", "65.80"),
    ("AUG", 1, 8, 18, "300.00", "13.70"),
    ("SEP", 2, 9, 9, "950.00", "41.90"),
    ("SEP2", 0, 9, 25, "2200.00", "96.10"),
    ("OCT", 1, 10, 6, "640.00", "28.40"),
    ("NOV", 0, 11, 4, "1000.00", "44.00"),
)
CLIENTS = (("Ava Stone", "USD"), ("Ben Lee", "GBP"), ("Cleo Diaz", "EUR"))


def seed_payments(session: Session) -> Session:
    with freeze_time(NOW):
        clients = [add_client(session, name, currency) for name, currency in CLIENTS]
        for tx_id, index, month, day, gross, fee in PAYMENTS:
            when = datetime(2026, month, day, 6, 30, tzinfo=UTC)
            add_tx(session, clients[index], tx_id, occurred_at=when, gross=gross, fee=fee)
        recalculate_leakage(session, FakeFxGateway())
    session.flush()
    return session


def ask(session: Session, question: str) -> ChatOut:
    with freeze_time(NOW):
        return answer_question(session, FakeLlm(), ChatIn(question=question), NOW)
