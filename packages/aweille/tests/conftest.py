from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

import pytest
from aweille.core import PlannedRun, SectionInput, Storage


@pytest.fixture
def storage() -> Storage:
    runs: dict[UUID, PlannedRun] = {}

    def insert_if_absent(run: PlannedRun) -> tuple[PlannedRun, bool]:
        if run.id in runs:
            return runs[run.id], False
        runs[run.id] = run
        return run, True

    def read_range(start: date, end: date) -> list[PlannedRun]:
        return list(
            reversed([r for r in runs.values() if start <= r.planned_date < end])
        )

    return cast(
        Storage,
        SimpleNamespace(insert_if_absent=insert_if_absent, read_range=read_range),
    )


@pytest.fixture
def run_input() -> dict[str, Any]:
    return {
        "id": UUID("54D97D4D-FADB-4D50-926E-AF1BB26C711A"),
        "planned_date": date(2026, 10, 14),
        "run_type": "interval",
        "sections": [
            SectionInput(Decimal("1.000"), 390),
            SectionInput(Decimal("1"), 345),
            SectionInput(Decimal("1"), 390),
        ],
        "user_note": "  Keep the first section easy.  ",
        "trainer_note": "  Finish relaxed.  ",
    }
