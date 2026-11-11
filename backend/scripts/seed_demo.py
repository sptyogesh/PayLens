"""Load or reset demo history labelled "Demo seed" (FR-040, FR-041).

Usage (from backend/):
    uv run python -m scripts.seed_demo           # add or refresh 24 demo rows, then leakage
    uv run python -m scripts.seed_demo --reset   # remove demo rows and all (demo) FIRAs
"""

import argparse

from app.api.deps import get_fx_gateway
from app.db import get_engine, get_session_factory
from app.models import Base
from app.services.fira_rematch import delete_all_firas
from app.services.refresh_service import safe_refresh
from app.services.seed_service import count_seed_rows, reset_seed
from app.services.seed_service import seed_demo as seed


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Load or reset PayLens demo seed data.")
    parser.add_argument("--reset", action="store_true", help="remove demo rows and FIRAs")
    args = parser.parse_args(argv)
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as session:
        if args.reset:
            firas = delete_all_firas(session)
            removed, clients = reset_seed(session)
            message = f"Removed {removed} demo transactions, {clients} demo clients"
            message += f" and {firas} FIRAs."
        else:
            added = seed(session)
            message = f"Added {added} demo transactions; {count_seed_rows(session)} in total."
        session.commit()
    summary = safe_refresh(get_session_factory(), get_fx_gateway())  # FR-020
    if summary is not None:
        message += f" Leakage: {summary.calculated} calculated, "
        message += f"{summary.rate_unavailable} waiting for an exchange rate."
    print(message)


if __name__ == "__main__":
    main()
