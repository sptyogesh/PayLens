"""scripts.generate_fira_samples: 21 demo PDFs with a readable marker (004 research R4)."""

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.common.constants import FIRA_FAKE_MARKER
from app.fakes.llm_fake_fira import read_marker
from scripts.generate_fira_samples import DEMO_LABEL, generate, main

NOW = datetime(2026, 11, 10, 6, 0, tzinfo=UTC)


def test_writes_21_pdfs_with_parseable_markers(tmp_path: Path) -> None:
    written = generate(tmp_path, NOW)
    assert len(written) == 21 and len(list(tmp_path.glob("*.pdf"))) == 21
    names = {path.name for path in written}
    assert "fira-SEED-0021.pdf" in names and "fira-SEED-0022.pdf" not in names
    for path in written:
        data = path.read_bytes()
        assert data.startswith(b"%PDF-")
        marker = read_marker(data)
        assert marker is not None and marker["reference_no"] == path.stem.removeprefix("fira-")
        assert re.fullmatch(r"\d+\.\d{2}", marker["foreign_amount"])


def test_sample_fields_follow_research_r4(tmp_path: Path) -> None:
    markers = {p.stem: read_marker(p.read_bytes()) or {} for p in generate(tmp_path, NOW)}
    first = markers["fira-SEED-0001"]
    assert first == {
        "currency": "USD",
        "foreign_amount": "1200.00",
        "inr_amount": "100800.00",
        "purpose_code": "P0802",
        "rate": "84.000000",
        "reference_no": "SEED-0001",
        "remittance_date": "2026-10-05",  # payment 3 Oct + 2 days
        "remitter": "PayPal (demo)",
    }
    assert markers["fira-SEED-0020"]["foreign_amount"] == "1184.50"  # 1150.00 x 1.03
    assert markers["fira-SEED-0021"]["remittance_date"] == "2026-07-25"  # 13 Jul + 12 days


def test_visible_demo_label_and_marker_text(tmp_path: Path) -> None:
    data = generate(tmp_path, NOW)[0].read_bytes()
    assert FIRA_FAKE_MARKER.encode() in data
    assert b"DEMO SAMPLE" in data and b"not a real bank document" in data
    assert DEMO_LABEL.startswith("DEMO SAMPLE")


def test_cli_prints_the_count(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["--out", str(tmp_path)])
    assert "Wrote 21 demo FIRA PDFs" in capsys.readouterr().out
