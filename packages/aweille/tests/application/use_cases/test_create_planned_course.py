from dataclasses import replace
from datetime import UTC, date, datetime, time
from typing import Any
from unittest.mock import create_autospec
from uuid import UUID

import pytest
from aweille.application import (
    CreatePlannedCourseCommand,
    InvalidPlannedCourse,
    PlannedCourseConflict,
    PlannedCourseRepository,
    SectionReadModel,
    StorageFailure,
    StorageUnavailable,
)
from aweille.domain import Distance, Pace, Section

SectionInput = CreatePlannedCourseCommand.InputData.SectionInput


@pytest.fixture
def repository() -> Any:
    repository = create_autospec(PlannedCourseRepository, instance=True)
    repository.save.side_effect = lambda planned_course: (planned_course, True)
    return repository


@pytest.fixture
def command(repository: Any) -> CreatePlannedCourseCommand:
    return CreatePlannedCourseCommand(repository)


@pytest.fixture
def input_data() -> CreatePlannedCourseCommand.InputData:
    return CreatePlannedCourseCommand.InputData(
        id=UUID("54d97d4d-fadb-4d50-926e-af1bb26c711a"),
        planned_date=date(2026, 10, 14),
        course_type="interval",
        sections=(
            SectionInput(metres=1000, seconds_per_km=390),
            SectionInput(metres=1000, seconds_per_km=345),
            SectionInput(metres=1000, seconds_per_km=390),
        ),
        planned_start_time=time(7, 30),
        user_note="  Keep the first section easy.  ",
        trainer_note="  Finish relaxed.  ",
    )


def test_creation_saves_normalized_values_and_reports_a_new_planned_course(
    command: CreatePlannedCourseCommand,
    repository: Any,
    input_data: CreatePlannedCourseCommand.InputData,
) -> None:
    """A new planned course is saved with trimmed notes and its exact sections."""
    output = command.execute(input_data)

    assert output == CreatePlannedCourseCommand.OutputData(
        id=UUID("54d97d4d-fadb-4d50-926e-af1bb26c711a"),
        planned_date=date(2026, 10, 14),
        planned_start_time=time(7, 30),
        course_type="interval",
        sections=(
            SectionReadModel(metres=1000, seconds_per_km=390),
            SectionReadModel(metres=1000, seconds_per_km=345),
            SectionReadModel(metres=1000, seconds_per_km=390),
        ),
        user_note="Keep the first section easy.",
        trainer_note="Finish relaxed.",
        revision=1,
        created=True,
    )
    saved = repository.save.call_args.args[0]
    assert saved.user_note == "Keep the first section easy."
    assert saved.trainer_note == "Finish relaxed."


def test_exact_numeric_targets_have_no_domain_upper_limit(
    command: CreatePlannedCourseCommand,
    input_data: CreatePlannedCourseCommand.InputData,
) -> None:
    """Huge whole-number targets pass through unchanged."""
    huge = (SectionInput(metres=10**5003, seconds_per_km=10**5000),)

    output = command.execute(replace(input_data, sections=huge))

    assert output.sections == (
        SectionReadModel(metres=10**5003, seconds_per_km=10**5000),
    )


def test_section_count_and_note_length_are_not_limited(
    command: CreatePlannedCourseCommand,
    input_data: CreatePlannedCourseCommand.InputData,
) -> None:
    """Many sections and long notes are accepted as given."""
    note = "x" * 1_048_577
    sections = (SectionInput(metres=1000, seconds_per_km=390),) * 1001

    output = command.execute(
        replace(input_data, sections=sections, user_note=note, trainer_note=note)
    )

    assert len(output.sections) == 1001
    assert output.user_note == note
    assert output.trainer_note == note


def test_notes_keep_internal_whitespace_and_blank_notes_become_absent(
    command: CreatePlannedCourseCommand,
    input_data: CreatePlannedCourseCommand.InputData,
) -> None:
    """Only outer whitespace is trimmed; a blank note is treated as absent."""
    output = command.execute(
        replace(
            input_data,
            user_note=" \n First  line\n\tSecond line. \t",
            trainer_note="   ",
        )
    )

    assert output.user_note == "First  line\n\tSecond line."
    assert output.trainer_note is None


@pytest.mark.parametrize(
    ("planned_date", "start_time"),
    [
        (date(2026, 3, 8), time(1, 59)),
        (date(2026, 3, 8), time(3)),
        (date(2026, 11, 1), time(1, 30, fold=1)),
        (date(2026, 1, 14), time(7, 30)),
        (date.min, time(0)),
        (date.max, time(23, 59)),
        (date(2026, 10, 14), None),
    ],
)
def test_valid_local_schedules_keep_the_time_without_selecting_an_occurrence(
    command: CreatePlannedCourseCommand,
    input_data: CreatePlannedCourseCommand.InputData,
    planned_date: date,
    start_time: time | None,
) -> None:
    """Existing Montreal times are kept, and a fall-back time selects no occurrence."""
    output = command.execute(
        replace(input_data, planned_date=planned_date, planned_start_time=start_time)
    )

    assert output.planned_date == planned_date
    assert output.planned_start_time == start_time
    if output.planned_start_time is not None:
        assert output.planned_start_time.fold == 0


@pytest.mark.parametrize(
    ("changes", "field_path", "code"),
    [
        ({"id": "54d97d4d-fadb-4d50-926e-af1bb26c711a"}, ("id",), "invalid_id"),
        ({"planned_date": "2026-10-14"}, ("planned_date",), "invalid_date"),
        ({"planned_date": datetime(2026, 10, 14)}, ("planned_date",), "invalid_date"),
        ({"course_type": "long_run"}, ("course_type",), "invalid_course_type"),
        ({"sections": ()}, ("sections",), "invalid_sections"),
        (
            {"sections": (SectionInput(metres=0, seconds_per_km=390),)},
            ("metres",),
            "invalid_distance",
        ),
        (
            {"sections": (SectionInput(metres=1000, seconds_per_km=True),)},
            ("seconds_per_km",),
            "invalid_pace",
        ),
        ({"user_note": 123}, ("user_note",), "invalid_note"),
        ({"trainer_note": True}, ("trainer_note",), "invalid_note"),
        (
            {"planned_start_time": time(7, 30, 1)},
            ("planned_start_time",),
            "invalid_start_time",
        ),
        (
            {"planned_start_time": time(7, 30, microsecond=1)},
            ("planned_start_time",),
            "invalid_start_time",
        ),
        (
            {"planned_start_time": time(7, 30, tzinfo=UTC)},
            ("planned_start_time",),
            "invalid_start_time",
        ),
        (
            {"planned_start_time": "07:30"},
            ("planned_start_time",),
            "invalid_start_time",
        ),
        (
            {"planned_date": date(2026, 3, 8), "planned_start_time": time(2)},
            ("planned_start_time",),
            "nonexistent_start_time",
        ),
        (
            {"planned_date": date(2026, 3, 8), "planned_start_time": time(2, 59)},
            ("planned_start_time",),
            "nonexistent_start_time",
        ),
    ],
)
def test_invalid_fields_report_safe_problems_before_saving(
    command: CreatePlannedCourseCommand,
    repository: Any,
    input_data: CreatePlannedCourseCommand.InputData,
    changes: dict[str, Any],
    field_path: tuple[str | int, ...],
    code: str,
) -> None:
    """An invalid field reports its path, code and message, and nothing is saved."""
    with pytest.raises(InvalidPlannedCourse) as failure:
        command.execute(replace(input_data, **changes))

    assert failure.value.problems[0].loc == field_path
    assert failure.value.problems[0].code == code
    assert failure.value.problems[0].message
    repository.save.assert_not_called()


def test_identical_retry_returns_the_saved_planned_course(
    command: CreatePlannedCourseCommand,
    repository: Any,
    input_data: CreatePlannedCourseCommand.InputData,
) -> None:
    """A retry matching the saved normalized values returns it, not created."""
    repository.save.side_effect = lambda planned_course: (
        replace(planned_course, revision=3),
        False,
    )

    output = command.execute(input_data)

    assert output.created is False
    assert output.revision == 3


@pytest.mark.parametrize(
    "changes",
    [
        {"planned_date": date(2026, 10, 15)},
        {"planned_start_time": None},
        {"user_note": "Changed user note"},
        {"sections": (Section(Distance(1000), Pace(390)),)},
    ],
)
def test_changed_retry_conflicts(
    command: CreatePlannedCourseCommand,
    repository: Any,
    input_data: CreatePlannedCourseCommand.InputData,
    changes: dict[str, Any],
) -> None:
    """A saved planned course with different values under the ID is a conflict."""
    repository.save.side_effect = lambda planned_course: (
        replace(planned_course, **changes),
        False,
    )

    with pytest.raises(PlannedCourseConflict):
        command.execute(input_data)


@pytest.mark.parametrize("error_type", [StorageUnavailable, StorageFailure])
def test_storage_failure_categories_reach_the_caller(
    command: CreatePlannedCourseCommand,
    repository: Any,
    input_data: CreatePlannedCourseCommand.InputData,
    error_type: type[Exception],
) -> None:
    """Storage failures keep their category so callers know whether to retry."""
    failure = error_type("Storage could not complete the operation.")
    repository.save.side_effect = failure

    with pytest.raises(error_type) as reported:
        command.execute(input_data)

    assert reported.value is failure
