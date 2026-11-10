"""Load or reset demo history labelled "Demo seed" (FR-040, FR-041).

Usage (from backend/):
    uv run python -m scripts.seed_demo           # add or refresh 24 demo rows
    uv run python -m scripts.seed_demo --reset   # remove demo rows only
"""

import argparse

from sqlalchemy.orm import Session

from app.common.dates import utc_now
from app.db import get_engine, get_session_factory
from app.models import Base
from app.services.seed_service import (
    count_seed_rows,
    months_before,
    reset_seed,
    upsert_seed_client,
    upsert_seed_transaction,
)
from scripts.seed_data import SEED_CLIENTS, seed_rows


def seed(session: Session) -> int:
    clients = [upsert_seed_client(session, client) for client in SEED_CLIENTS]
    now = utc_now()
    added = 0
    for row in seed_rows():
        when = months_before(now, row.months_ago, row.day)
        added += upsert_seed_transaction(
            session, row.seed_id, clients[row.client_index], when, row.gross
        )
    return added


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Load or reset PayLens demo seed data.")
    parser.add_argument("--reset", action="store_true", help="remove demo_seed rows only")
    args = parser.parse_args(argv)
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as session:
        if args.reset:
            removed, clients = reset_seed(session)
            message = f"Removed {removed} demo transactions and {clients} demo clients."
        else:
            added = seed(session)
            message = f"Added {added} demo transactions; {count_seed_rows(session)} in total."
        session.commit()
    print(message)


if __name__ == "__main__":
    main()
