from datetime import date, time
from typing import Any
from unittest.mock import create_autospec
from uuid import UUID

import pytest
from aweille.application import (
    InvalidPlannedCourse,
    PlannedCourseNotFound,
    PlannedCourseReader,
    PlannedCourseReadModel,
    ReadPlannedCourseQuery,
    SectionReadModel,
    StorageUnavailable,
)

ID = UUID("54d97d4d-fadb-4d50-926e-af1bb26c711a")


@pytest.fixture
def read_model() -> PlannedCourseReadModel:
    return PlannedCourseReadModel(
        id=ID,
        planned_date=date(2026, 10, 14),
        planned_start_time=time(7, 30),
        course_type="easy",
        sections=(SectionReadModel(metres=5000, seconds_per_km=390),),
        user_note="Keep it easy.",
        trainer_note=None,
        revision=2,
    )


@pytest.fixture
def reader(read_model: PlannedCourseReadModel) -> Any:
    # Any: autospec mocks expose Mock attributes that the port type hides.
    reader = create_autospec(PlannedCourseReader, instance=True)
    reader.read.return_value = read_model
    return reader


@pytest.fixture
def query(reader: Any) -> ReadPlannedCourseQuery:
    return ReadPlannedCourseQuery(reader)


def test_read_returns_the_saved_planned_course_and_revision(
    query: ReadPlannedCourseQuery, reader: Any
) -> None:
    """A saved planned course is returned with its current revision."""
    output = query.execute(ReadPlannedCourseQuery.InputData(id=ID))

    assert output == ReadPlannedCourseQuery.OutputData(
        id=ID,
        planned_date=date(2026, 10, 14),
        planned_start_time=time(7, 30),
        course_type="easy",
        sections=(SectionReadModel(metres=5000, seconds_per_km=390),),
        user_note="Keep it easy.",
        trainer_note=None,
        revision=2,
    )
    reader.read.assert_called_once_with(ID)


def test_absent_planned_course_is_not_found(
    query: ReadPlannedCourseQuery, reader: Any
) -> None:
    """An ID with no saved planned course reports it missing."""
    reader.read.return_value = None

    with pytest.raises(PlannedCourseNotFound):
        query.execute(ReadPlannedCourseQuery.InputData(id=ID))


def test_invalid_id_is_rejected_before_reading(
    query: ReadPlannedCourseQuery, reader: Any
) -> None:
    """A non-UUID ID reports its field and reads nothing."""
    with pytest.raises(InvalidPlannedCourse) as failure:
        query.execute(ReadPlannedCourseQuery.InputData(id=str(ID)))  # ty: ignore[invalid-argument-type]

    assert failure.value.problems[0].loc == ("id",)
    reader.read.assert_not_called()


def test_storage_failure_reaches_the_caller(
    query: ReadPlannedCourseQuery, reader: Any
) -> None:
    """A storage failure keeps its category so the caller can retry."""
    failure = StorageUnavailable("Storage unavailable.")
    reader.read.side_effect = failure

    with pytest.raises(StorageUnavailable) as reported:
        query.execute(ReadPlannedCourseQuery.InputData(id=ID))

    assert reported.value is failure
