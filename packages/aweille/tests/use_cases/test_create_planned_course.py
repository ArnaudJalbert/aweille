from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, time
from typing import Any
from unittest.mock import Mock

import pytest
from aweille.core import (
    CourseType,
    Distance,
    Pace,
    PlannedCourseConflict,
    PlannedCourseStorage,
    Section,
    StorageFailure,
    StorageUnavailable,
    ValidationError,
    create_planned_course,
    read_planned_courses,
)


def test_created_planned_course_can_be_read_with_exact_ordered_targets(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    planned_course, inserted = create_planned_course(
        storage, **planned_course_input, planned_start_time=time(7, 30)
    )

    assert inserted is True
    assert str(planned_course.id) == "54d97d4d-fadb-4d50-926e-af1bb26c711a"
    assert planned_course.planned_date == date(2026, 10, 14)
    assert planned_course.planned_start_time == time(7, 30)
    assert planned_course.course_type is CourseType.INTERVAL
    assert [
        (s.distance.metres, s.target_pace.seconds_per_km)
        for s in planned_course.sections
    ] == [
        (1000, 390),
        (1000, 345),
        (1000, 390),
    ]
    assert planned_course.user_note == "Keep the first section easy."
    assert planned_course.trainer_note == "Finish relaxed."
    assert read_planned_courses(
        storage, start=date(2026, 10, 12), end=date(2026, 10, 19)
    ) == [planned_course]


def test_exact_numeric_targets_have_no_domain_upper_limit(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    planned_course_input["sections"] = [Section(Distance(10**5003), Pace(10**5000))]
    planned_course, _ = create_planned_course(storage, **planned_course_input)

    assert planned_course.sections[0].distance.metres == 10**5003
    assert planned_course.sections[0].target_pace.seconds_per_km == 10**5000
    assert create_planned_course(storage, **planned_course_input) == (
        planned_course,
        False,
    )


@pytest.mark.parametrize(
    ("field", "value", "field_path", "code"),
    [
        ("id", "54d97d4d-fadb-4d50-926e-af1bb26c711a", ("id",), "invalid_id"),
        ("planned_date", "2026-10-14", ("planned_date",), "invalid_date"),
        ("planned_date", datetime(2026, 10, 14), ("planned_date",), "invalid_date"),
        ("course_type", "long_run", ("course_type",), "invalid_course_type"),
        ("course_type", "easy", ("course_type",), "invalid_course_type"),
        ("course_type", ["easy"], ("course_type",), "invalid_course_type"),
        ("sections", [], ("sections",), "invalid_sections"),
        ("sections", None, ("sections",), "invalid_sections"),
        ("sections", "1 km", ("sections",), "invalid_sections"),
        ("sections", [None], ("sections", 0), "invalid_section"),
        ("user_note", 123, ("user_note",), "invalid_note"),
        ("trainer_note", True, ("trainer_note",), "invalid_note"),
    ],
)
def test_invalid_fields_report_safe_problems_before_saving(
    storage: PlannedCourseStorage,
    planned_course_input: dict[str, Any],
    field: str,
    value: Any,
    field_path: tuple[str | int, ...],
    code: str,
) -> None:
    planned_course_input[field] = value

    with pytest.raises(ValidationError) as failure:
        create_planned_course(storage, **planned_course_input)

    assert failure.value.problems[0].loc == field_path
    assert failure.value.problems[0].code == code
    assert failure.value.problems[0].message
    assert (
        read_planned_courses(storage, start=date(2026, 10, 12), end=date(2026, 10, 19))
        == []
    )


@pytest.mark.parametrize(
    "start_time",
    [
        time(7, 30, 1),
        time(7, 30, microsecond=1),
        time(7, 30, tzinfo=UTC),
        "07:30",
    ],
)
def test_start_time_requires_a_local_minute_precision_time(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any], start_time: Any
) -> None:
    with pytest.raises(ValidationError) as failure:
        create_planned_course(
            storage, **planned_course_input, planned_start_time=start_time
        )

    assert failure.value.problems[0].loc == ("planned_start_time",)
    assert failure.value.problems[0].code == "invalid_start_time"
    assert (
        read_planned_courses(storage, start=date(2026, 10, 12), end=date(2026, 10, 19))
        == []
    )


@pytest.mark.parametrize("start_time", [time(2), time(2, 59)])
def test_montreal_spring_forward_gap_rejects_nonexistent_start_times(
    storage: PlannedCourseStorage,
    planned_course_input: dict[str, Any],
    start_time: time,
) -> None:
    planned_course_input["planned_date"] = date(2026, 3, 8)
    with pytest.raises(ValidationError) as failure:
        create_planned_course(
            storage, **planned_course_input, planned_start_time=start_time
        )

    assert failure.value.problems[0].code == "nonexistent_start_time"
    assert (
        read_planned_courses(storage, start=date(2026, 3, 8), end=date(2026, 3, 9))
        == []
    )


def test_identical_retry_compares_normalized_values_and_returns_existing_planned_course(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    planned_course_input["user_note"] = " \n \t "
    planned_course_input.pop("trainer_note")
    original, inserted = create_planned_course(storage, **planned_course_input)
    assert inserted is True

    planned_course_input["sections"] = [
        Section(Distance(1000), Pace(390)),
        Section(Distance(1000), Pace(345)),
        Section(Distance(1000), Pace(390)),
    ]
    planned_course_input["user_note"] = None
    planned_course_input["trainer_note"] = None
    retried, inserted = create_planned_course(
        storage, **planned_course_input, planned_start_time=None
    )

    assert retried == original
    assert inserted is False
    assert original.user_note is None
    assert original.trainer_note is None
    assert original.planned_start_time is None
    assert read_planned_courses(
        storage, start=date(2026, 10, 12), end=date(2026, 10, 19)
    ) == [original]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("planned_date", date(2026, 10, 15)),
        ("planned_start_time", time(7, 30)),
        ("course_type", CourseType.EASY),
        ("user_note", "Changed user note"),
        ("trainer_note", "Changed trainer note"),
        ("distance", Distance(1001)),
        ("target_pace", Pace(391)),
        (
            "sections",
            [
                Section(Distance(1000), Pace(345)),
                Section(Distance(1000), Pace(390)),
                Section(Distance(1000), Pace(390)),
            ],
        ),
        (
            "sections",
            [Section(Distance(1000), Pace(390)), Section(Distance(1000), Pace(345))],
        ),
    ],
)
def test_changed_retry_conflicts_and_leaves_saved_planned_course_untouched(
    storage: PlannedCourseStorage,
    planned_course_input: dict[str, Any],
    field: str,
    value: Any,
) -> None:
    original, _ = create_planned_course(storage, **planned_course_input)
    if field in ("distance", "target_pace"):
        planned_course_input["sections"][0] = replace(
            planned_course_input["sections"][0], **{field: value}
        )
    else:
        planned_course_input[field] = value

    with pytest.raises(PlannedCourseConflict):
        create_planned_course(storage, **planned_course_input)

    assert read_planned_courses(
        storage, start=date(2026, 10, 12), end=date(2026, 10, 19)
    ) == [original]


def test_saved_targets_and_notes_cannot_be_changed_through_returned_values(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    planned_course, _ = create_planned_course(storage, **planned_course_input)
    planned_course_input["sections"].clear()

    for value, field, replacement in [
        (planned_course, "user_note", "Changed"),
        (planned_course.sections[0], "distance", Distance(2000)),
        (planned_course.sections[0].distance, "metres", 2000),
        (planned_course.sections[0].target_pace, "seconds_per_km", 400),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, replacement)

    assert len(planned_course.sections) == 3
    assert read_planned_courses(
        storage, start=date(2026, 10, 12), end=date(2026, 10, 19)
    ) == [planned_course]


def test_invalid_inputs_are_rejected_even_when_storage_is_unavailable(
    planned_course_input: dict[str, Any],
) -> None:
    storage = Mock(spec=PlannedCourseStorage)
    storage.save.side_effect = StorageUnavailable("Storage unavailable.")
    planned_course_input["sections"][1] = None

    with pytest.raises(ValidationError):
        create_planned_course(storage, **planned_course_input)


@pytest.mark.parametrize(
    ("planned_date", "start_time"),
    [
        (date(2026, 3, 8), time(1, 59)),
        (date(2026, 3, 8), time(3)),
        (date(2026, 11, 1), time(1, 30, fold=1)),
        (date(2026, 1, 14), time(7, 30)),
        (date.min, time(0)),
        (date.max, time(23, 59)),
    ],
)
def test_valid_local_schedules_keep_the_date_and_time_without_selecting_an_occurrence(
    storage: PlannedCourseStorage,
    planned_course_input: dict[str, Any],
    planned_date: date,
    start_time: time | None,
) -> None:
    planned_course_input.update(
        planned_date=planned_date, planned_start_time=start_time
    )
    planned_course, _ = create_planned_course(storage, **planned_course_input)
    expected_time = start_time.replace(fold=0) if start_time is not None else None

    assert planned_course.planned_date == planned_date
    assert planned_course.planned_start_time == expected_time
    if planned_course.planned_start_time is not None:
        assert planned_course.planned_start_time.tzinfo is None
        assert planned_course.planned_start_time.fold == 0
    planned_course_input["planned_start_time"] = expected_time
    assert create_planned_course(storage, **planned_course_input) == (
        planned_course,
        False,
    )


@pytest.mark.parametrize("course_type", list(CourseType))
def test_course_type_does_not_impose_section_rules(
    storage: PlannedCourseStorage,
    planned_course_input: dict[str, Any],
    course_type: Any,
) -> None:
    planned_course_input.update(
        course_type=course_type, sections=[Section(Distance(1), Pace(1))]
    )
    planned_course, _ = create_planned_course(storage, **planned_course_input)

    assert planned_course.course_type == course_type
    assert len(planned_course.sections) == 1
    assert planned_course.sections[0].distance.metres == 1


def test_notes_preserve_internal_whitespace_and_line_breaks(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    planned_course_input.update(
        user_note=" \n First  line\n\tSecond line. \t", trainer_note="   "
    )
    planned_course, _ = create_planned_course(storage, **planned_course_input)

    assert planned_course.user_note == "First  line\n\tSecond line."
    assert planned_course.trainer_note is None
    planned_course_input.update(user_note=planned_course.user_note, trainer_note=None)
    assert create_planned_course(storage, **planned_course_input) == (
        planned_course,
        False,
    )


def test_core_does_not_limit_section_count_or_note_length(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    note = "x" * 1_048_577
    planned_course_input.update(
        sections=[Section(Distance(1000), Pace(390))] * 1001,
        user_note=note,
        trainer_note=note,
    )
    planned_course, _ = create_planned_course(storage, **planned_course_input)

    assert len(planned_course.sections) == 1001
    assert planned_course.user_note == note
    assert planned_course.trainer_note == note


@pytest.mark.parametrize("error_type", [StorageUnavailable, StorageFailure])
def test_storage_failure_categories_reach_the_public_caller(
    planned_course_input: dict[str, Any], error_type: type[Exception]
) -> None:
    failure = error_type("Storage could not complete the operation.")
    storage = Mock(spec=PlannedCourseStorage)
    storage.save.side_effect = failure

    with pytest.raises(error_type) as reported:
        create_planned_course(storage, **planned_course_input)

    assert reported.value is failure
