from datetime import date, datetime, time
from typing import Any
from unittest.mock import Mock
from uuid import UUID

import pytest
from aweille.core import (
    PlannedCourseStorage,
    StorageFailure,
    StorageUnavailable,
    ValidationError,
    create_planned_course,
    read_planned_courses,
)


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
def test_invalid_read_range_reports_field_problems(
    start: Any,
    end: Any,
    field_path: tuple[str | int, ...],
    code: str,
) -> None:
    storage = Mock(spec=PlannedCourseStorage)
    storage.get.side_effect = StorageUnavailable("Storage unavailable.")

    with pytest.raises(ValidationError) as failure:
        read_planned_courses(storage, start=start, end=end)

    assert failure.value.problems[0].loc == field_path
    assert failure.value.problems[0].code == code


def test_read_range_is_half_open_and_orders_dates_times_then_canonical_ids(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    for number, planned_date, start_time in [
        (3, date(2026, 10, 12), time(8)),
        (1, date(2026, 10, 12), time(7, 30)),
        (5, date(2026, 10, 13), time(0)),
        (4, date(2026, 10, 12), None),
        (2, date(2026, 10, 12), time(7, 30)),
        (6, date(2026, 10, 11), time(23, 59)),
        (7, date(2026, 10, 19), time(0)),
    ]:
        planned_course_input.update(
            id=UUID(int=number),
            planned_date=planned_date,
            planned_start_time=start_time,
        )
        _, inserted = create_planned_course(storage, **planned_course_input)
        assert inserted is True

    planned_courses = read_planned_courses(
        storage, start=date(2026, 10, 12), end=date(2026, 10, 19)
    )
    assert [r.id for r in planned_courses] == [UUID(int=n) for n in [1, 2, 3, 4, 5]]
    assert (
        read_planned_courses(storage, start=date(2026, 10, 14), end=date(2026, 10, 15))
        == []
    )


@pytest.mark.parametrize("error_type", [StorageUnavailable, StorageFailure])
def test_storage_failure_categories_reach_the_public_caller(
    error_type: type[Exception],
) -> None:
    failure = error_type("Storage could not complete the operation.")
    storage = Mock(spec=PlannedCourseStorage)
    storage.get.side_effect = failure

    with pytest.raises(error_type) as reported:
        read_planned_courses(storage, start=date(2026, 10, 12), end=date(2026, 10, 19))

    assert reported.value is failure
