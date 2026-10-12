from datetime import date
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from aweille.core import PlannedRun, Storage


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
