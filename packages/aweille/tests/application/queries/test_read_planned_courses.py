from datetime import date, datetime, time
from typing import Any
from unittest.mock import create_autospec
from uuid import UUID

import pytest
from aweille.application import (
    InvalidPlannedCourse,
    PlannedCourseReader,
    PlannedCourseReadModel,
    ReadPlannedCoursesQuery,
    SectionReadModel,
    StorageFailure,
    StorageUnavailable,
)

WEEK = ReadPlannedCoursesQuery.InputData(
    start=date(2026, 10, 12), end=date(2026, 10, 19)
)


@pytest.fixture
def reader() -> Any:
    reader = create_autospec(PlannedCourseReader, instance=True)
    reader.read_range.return_value = []
    return reader


@pytest.fixture
def query(reader: Any) -> ReadPlannedCoursesQuery:
    return ReadPlannedCoursesQuery(reader)


def test_range_orders_dates_then_times_with_untimed_last_then_canonical_ids(
    query: ReadPlannedCoursesQuery, reader: Any
) -> None:
    """Planned courses come back in schedule order whatever order storage used."""
    reader.read_range.return_value = [
        _read_model(3, date(2026, 10, 12), time(8)),
        _read_model(1, date(2026, 10, 12), time(7, 30)),
        _read_model(5, date(2026, 10, 13), time(0)),
        _read_model(4, date(2026, 10, 12), None),
        _read_model(2, date(2026, 10, 12), time(7, 30)),
    ]

    output = query.execute(WEEK)

    assert [planned_course.id for planned_course in output.planned_courses] == [
        UUID(int=number) for number in [1, 2, 3, 4, 5]
    ]
    reader.read_range.assert_called_once_with(date(2026, 10, 12), date(2026, 10, 19))


def test_empty_range_returns_no_planned_courses(query: ReadPlannedCoursesQuery) -> None:
    """A range with nothing planned returns an empty tuple."""
    assert query.execute(WEEK).planned_courses == ()


@pytest.mark.parametrize(
    ("start", "end", "field_path", "code"),
    [
        (date(2026, 10, 12), date(2026, 10, 12), ("end",), "invalid_range"),
        (date(2026, 10, 19), date(2026, 10, 12), ("end",), "invalid_range"),
        (date(2026, 10, 12), None, ("end",), "invalid_date"),
        ("2026-10-12", date(2026, 10, 19), ("start",), "invalid_date"),
        (datetime(2026, 10, 12), date(2026, 10, 19), ("start",), "invalid_date"),
    ],
)
def test_invalid_range_reports_field_problems_before_reading(
    query: ReadPlannedCoursesQuery,
    reader: Any,
    start: Any,
    end: Any,
    field_path: tuple[str, ...],
    code: str,
) -> None:
    """An invalid boundary or an empty range reports its field and reads nothing."""
    with pytest.raises(InvalidPlannedCourse) as failure:
        query.execute(ReadPlannedCoursesQuery.InputData(start=start, end=end))

    assert failure.value.problems[0].loc == field_path
    assert failure.value.problems[0].code == code
    reader.read_range.assert_not_called()


@pytest.mark.parametrize("error_type", [StorageUnavailable, StorageFailure])
def test_storage_failure_categories_reach_the_caller(
    query: ReadPlannedCoursesQuery, reader: Any, error_type: type[Exception]
) -> None:
    """Storage failures keep their category so callers know whether to retry."""
    failure = error_type("Storage could not complete the read.")
    reader.read_range.side_effect = failure

    with pytest.raises(error_type) as reported:
        query.execute(WEEK)

    assert reported.value is failure


def _read_model(
    number: int, planned_date: date, start_time: time | None
) -> PlannedCourseReadModel:
    return PlannedCourseReadModel(
        id=UUID(int=number),
        planned_date=planned_date,
        planned_start_time=start_time,
        course_type="easy",
        sections=(SectionReadModel(metres=5000, seconds_per_km=390),),
        user_note=None,
        trainer_note=None,
        revision=1,
    )
