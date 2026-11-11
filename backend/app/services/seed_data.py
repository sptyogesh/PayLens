"""Fixed demo seed rows (FR-040, FR-042): fictional clients only, never real people."""

from dataclasses import dataclass
from decimal import Decimal

SEED_CLIENTS = (
    ("Northwind Studio (demo)", "northwind.us@example.com", "US", "USD"),
    ("Brightline Media (demo)", "brightline.uk@example.com", "GB", "GBP"),
    ("Kraft & Klang GmbH (demo)", "kraftklang.de@example.com", "DE", "EUR"),
    ("Coral Bay Apps (demo)", "coralbay.au@example.com", "AU", "AUD"),
)

# (client index, months before the current month, day of month, gross amount)
SEED_ROWS = (
    (0, 1, 3, "1200.00"), (1, 1, 7, "640.00"), (2, 1, 11, "980.00"),
    (3, 1, 15, "1450.00"), (0, 1, 20, "450.00"), (2, 1, 26, "310.00"),
    (1, 2, 2, "820.00"), (0, 2, 6, "1500.00"), (3, 2, 10, "760.00"),
    (2, 2, 14, "1120.00"), (1, 2, 19, "275.00"), (0, 2, 24, "690.00"),
    (3, 3, 4, "1320.00"), (2, 3, 8, "540.00"), (0, 3, 12, "2100.00"),
    (1, 3, 17, "930.00"), (3, 3, 21, "410.00"), (2, 3, 27, "860.00"),
    (0, 4, 5, "780.00"), (1, 4, 9, "1150.00"), (2, 4, 13, "720.00"),
    (3, 4, 18, "990.00"), (0, 4, 22, "360.00"), (1, 4, 27, "505.00"),
)  # fmt: skip


@dataclass(frozen=True)
class SeedRow:
    seed_id: str
    client_index: int
    months_ago: int
    day: int
    gross: Decimal


def seed_rows() -> list[SeedRow]:
    return [
        SeedRow(f"SEED-{n:04d}", client, months, day, Decimal(gross))
        for n, (client, months, day, gross) in enumerate(SEED_ROWS, start=1)
    ]
