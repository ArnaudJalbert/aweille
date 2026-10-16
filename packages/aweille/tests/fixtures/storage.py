from dataclasses import replace
from datetime import date
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from aweille.core import PlannedRun, RunNotFound, RunRevisionConflict, RunStorage


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

    def load(id: UUID) -> PlannedRun | None:
        return runs.get(id)

    def replace_run(run: PlannedRun, *, expected_revision: int) -> PlannedRun:
        current = runs.get(run.id)
        if current is None:
            raise RunNotFound
        if current.revision != expected_revision:
            raise RunRevisionConflict
        if current.to_dict() | {"revision": "1"} != run.to_dict() | {"revision": "1"}:
            current = replace(run, revision=current.revision + 1)
            runs[run.id] = current
        return current

    return cast(
        RunStorage,
        SimpleNamespace(save=save, get=get, load=load, replace=replace_run),
    )
