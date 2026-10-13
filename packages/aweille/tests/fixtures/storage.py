from datetime import date
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from aweille.core import PlannedRun, RunStorage


@pytest.fixture
def storage() -> RunStorage:
    runs: dict[UUID, PlannedRun] = {}

    def save(run: PlannedRun) -> tuple[PlannedRun, bool]:
        if run.id in runs:
            return runs[run.id], False
        runs[run.id] = run
        return run, True

    def get(start: date, end: date) -> list[PlannedRun]:
        return list(
            reversed([r for r in runs.values() if start <= r.planned_date < end])
        )

    return cast(
        RunStorage,
        SimpleNamespace(save=save, get=get),
    )
