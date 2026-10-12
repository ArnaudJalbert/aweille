from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, time
from decimal import Decimal, localcontext
from typing import Any
from unittest.mock import Mock

import pytest
from aweille.core import (
    RunConflict,
    SectionInput,
    Storage,
    StorageFailure,
    StorageUnavailable,
    ValidationError,
    create_run,
    read_runs,
)


def test_created_planned_run_can_be_read_with_exact_ordered_targets(
    storage: Storage, run_input: dict[str, Any]
) -> None:
    run, inserted = create_run(storage, **run_input, planned_start_time=time(7, 30))

    assert inserted is True
    assert str(run.id) == "54d97d4d-fadb-4d50-926e-af1bb26c711a"
    assert run.planned_date == date(2026, 10, 14)
    assert run.planned_start_time == time(7, 30)
    assert run.run_type == "interval"
    assert [(s.distance_m, s.target_pace_seconds_per_km) for s in run.sections] == [
        (1000, 390),
        (1000, 345),
        (1000, 390),
    ]
    assert run.user_note == "Keep the first section easy."
    assert run.trainer_note == "Finish relaxed."
    assert read_runs(storage, start=date(2026, 10, 12), end=date(2026, 10, 19)) == [run]


@pytest.mark.parametrize(
    "distance",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("0.0001"),
        Decimal("1.0001"),
        Decimal("NaN"),
        Decimal("sNaN"),
        Decimal("Infinity"),
        1,
        1.0,
        "1",
    ],
)
def test_invalid_distance_rejects_the_whole_run(
    storage: Storage, run_input: dict[str, Any], distance: Any
) -> None:
    run_input["sections"][1] = SectionInput(distance, 345)

    with pytest.raises(ValidationError) as failure:
        create_run(storage, **run_input)

    problem = failure.value.problems[0]
    assert problem.loc == ("sections", 1, "distance_km")
    assert problem.code == "invalid_distance"
    assert read_runs(storage, start=date(2026, 10, 12), end=date(2026, 10, 19)) == []


@pytest.mark.parametrize(
    ("distance", "expected_m"),
    [
        pytest.param(Decimal("0.001"), 1, id="one-metre"),
        pytest.param(
            Decimal("123456789012345678901234567890.123"),
            123456789012345678901234567890123,
            id="beyond-decimal-context",
        ),
        pytest.param(Decimal("1e5000"), 10**5003, id="unbounded-distance"),
    ],
)
def test_exact_numeric_targets_have_no_domain_upper_limit(
    storage: Storage, run_input: dict[str, Any], distance: Decimal, expected_m: int
) -> None:
    run_input["sections"] = [SectionInput(distance, 10**5000)]
    with localcontext() as context:
        context.prec = 2
        run, _ = create_run(storage, **run_input)

    assert run.sections[0].distance_m == expected_m
    assert run.sections[0].target_pace_seconds_per_km == 10**5000


@pytest.mark.parametrize("pace", [0, -1, 390.5, 390.0, Decimal("390"), "390", True])
def test_invalid_pace_rejects_the_whole_run(
    storage: Storage, run_input: dict[str, Any], pace: Any
) -> None:
    run_input["sections"][1] = SectionInput(Decimal("1"), pace)

    with pytest.raises(ValidationError) as failure:
        create_run(storage, **run_input)

    problem = failure.value.problems[0]
    assert problem.loc == ("sections", 1, "target_pace_seconds_per_km")
    assert problem.code == "invalid_pace"
    assert read_runs(storage, start=date(2026, 10, 12), end=date(2026, 10, 19)) == []


@pytest.mark.parametrize(
    ("field", "value", "loc", "code"),
    [
        ("id", "54d97d4d-fadb-4d50-926e-af1bb26c711a", ("id",), "invalid_id"),
        ("planned_date", "2026-10-14", ("planned_date",), "invalid_date"),
        ("planned_date", datetime(2026, 10, 14), ("planned_date",), "invalid_date"),
        ("run_type", "long_run", ("run_type",), "invalid_run_type"),
        ("run_type", ["easy"], ("run_type",), "invalid_run_type"),
        ("sections", [], ("sections",), "invalid_sections"),
        ("sections", None, ("sections",), "invalid_sections"),
        ("sections", "1 km", ("sections",), "invalid_sections"),
        ("sections", [None], ("sections", 0), "invalid_section"),
        ("user_note", 123, ("user_note",), "invalid_note"),
        ("trainer_note", True, ("trainer_note",), "invalid_note"),
    ],
)
def test_invalid_fields_report_safe_problems_before_saving(
    storage: Storage,
    run_input: dict[str, Any],
    field: str,
    value: Any,
    loc: tuple[str | int, ...],
    code: str,
) -> None:
    run_input[field] = value

    with pytest.raises(ValidationError) as failure:
        create_run(storage, **run_input)

    assert failure.value.problems[0].loc == loc
    assert failure.value.problems[0].code == code
    assert failure.value.problems[0].message
    assert read_runs(storage, start=date(2026, 10, 12), end=date(2026, 10, 19)) == []


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
    storage: Storage, run_input: dict[str, Any], start_time: Any
) -> None:
    with pytest.raises(ValidationError) as failure:
        create_run(storage, **run_input, planned_start_time=start_time)

    assert failure.value.problems[0].loc == ("planned_start_time",)
    assert failure.value.problems[0].code == "invalid_start_time"
    assert read_runs(storage, start=date(2026, 10, 12), end=date(2026, 10, 19)) == []


@pytest.mark.parametrize("start_time", [time(2), time(2, 59)])
def test_montreal_spring_forward_gap_rejects_nonexistent_start_times(
    storage: Storage, run_input: dict[str, Any], start_time: time
) -> None:
    run_input["planned_date"] = date(2026, 3, 8)
    with pytest.raises(ValidationError) as failure:
        create_run(storage, **run_input, planned_start_time=start_time)

    assert failure.value.problems[0].code == "nonexistent_start_time"
    assert read_runs(storage, start=date(2026, 3, 8), end=date(2026, 3, 9)) == []


def test_identical_retry_compares_normalized_values_and_returns_existing_run(
    storage: Storage, run_input: dict[str, Any]
) -> None:
    run_input["user_note"] = " \n \t "
    run_input.pop("trainer_note")
    original, inserted = create_run(storage, **run_input)
    assert inserted is True

    run_input["sections"] = [
        SectionInput(Decimal("1"), 390),
        SectionInput(Decimal("1.000"), 345),
        SectionInput(Decimal("1.000"), 390),
    ]
    run_input["user_note"] = None
    run_input["trainer_note"] = None
    retried, inserted = create_run(storage, **run_input, planned_start_time=None)

    assert retried == original
    assert inserted is False
    assert original.user_note is None
    assert original.trainer_note is None
    assert original.planned_start_time is None
    assert read_runs(storage, start=date(2026, 10, 12), end=date(2026, 10, 19)) == [
        original
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("planned_date", date(2026, 10, 15)),
        ("planned_start_time", time(7, 30)),
        ("run_type", "easy"),
        ("user_note", "Changed user note"),
        ("trainer_note", "Changed trainer note"),
        ("distance_km", Decimal("1.001")),
        ("target_pace_seconds_per_km", 391),
        (
            "sections",
            [
                SectionInput(Decimal("1"), 345),
                SectionInput(Decimal("1"), 390),
                SectionInput(Decimal("1"), 390),
            ],
        ),
        (
            "sections",
            [SectionInput(Decimal("1"), 390), SectionInput(Decimal("1"), 345)],
        ),
    ],
)
def test_changed_retry_conflicts_and_leaves_saved_run_untouched(
    storage: Storage, run_input: dict[str, Any], field: str, value: Any
) -> None:
    original, _ = create_run(storage, **run_input)
    if field in ("distance_km", "target_pace_seconds_per_km"):
        run_input["sections"][0] = replace(run_input["sections"][0], **{field: value})
    else:
        run_input[field] = value

    with pytest.raises(RunConflict):
        create_run(storage, **run_input)

    assert read_runs(storage, start=date(2026, 10, 12), end=date(2026, 10, 19)) == [
        original
    ]


def test_saved_targets_and_notes_cannot_be_changed_through_returned_values(
    storage: Storage, run_input: dict[str, Any]
) -> None:
    run, _ = create_run(storage, **run_input)
    run_input["sections"].clear()

    for value, field, replacement in [
        (run, "user_note", "Changed"),
        (run.sections[0], "distance_m", 2000),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, replacement)

    assert len(run.sections) == 3
    assert read_runs(storage, start=date(2026, 10, 12), end=date(2026, 10, 19)) == [run]


def test_invalid_inputs_are_rejected_even_when_storage_is_unavailable(
    run_input: dict[str, Any],
) -> None:
    storage = Mock(spec=Storage)
    storage.insert_if_absent.side_effect = StorageUnavailable("Storage unavailable.")
    run_input["sections"][1] = SectionInput(Decimal("1.0001"), 345)

    with pytest.raises(ValidationError):
        create_run(storage, **run_input)


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
    storage: Storage,
    run_input: dict[str, Any],
    planned_date: date,
    start_time: time | None,
) -> None:
    run_input.update(planned_date=planned_date, planned_start_time=start_time)
    run, _ = create_run(storage, **run_input)
    expected_time = start_time.replace(fold=0) if start_time is not None else None

    assert run.planned_date == planned_date
    assert run.planned_start_time == expected_time
    if run.planned_start_time is not None:
        assert run.planned_start_time.tzinfo is None
        assert run.planned_start_time.fold == 0
    run_input["planned_start_time"] = expected_time
    assert create_run(storage, **run_input) == (run, False)


@pytest.mark.parametrize("run_type", ["easy", "hard", "interval", "long"])
def test_run_type_does_not_impose_section_rules(
    storage: Storage, run_input: dict[str, Any], run_type: Any
) -> None:
    run_input.update(run_type=run_type, sections=[SectionInput(Decimal("0.001"), 1)])
    run, _ = create_run(storage, **run_input)

    assert run.run_type == run_type
    assert len(run.sections) == 1
    assert run.sections[0].distance_m == 1


def test_notes_preserve_internal_whitespace_and_line_breaks(
    storage: Storage, run_input: dict[str, Any]
) -> None:
    run_input.update(user_note=" \n First  line\n\tSecond line. \t", trainer_note="   ")
    run, _ = create_run(storage, **run_input)

    assert run.user_note == "First  line\n\tSecond line."
    assert run.trainer_note is None
    run_input.update(user_note=run.user_note, trainer_note=None)
    assert create_run(storage, **run_input) == (run, False)


def test_core_does_not_limit_section_count_or_note_length(
    storage: Storage, run_input: dict[str, Any]
) -> None:
    note = "x" * 1_048_577
    run_input.update(
        sections=[SectionInput(Decimal("1"), 390)] * 1001,
        user_note=note,
        trainer_note=note,
    )
    run, _ = create_run(storage, **run_input)

    assert len(run.sections) == 1001
    assert run.user_note == note
    assert run.trainer_note == note


@pytest.mark.parametrize("error_type", [StorageUnavailable, StorageFailure])
def test_storage_failure_categories_reach_the_public_caller(
    run_input: dict[str, Any], error_type: type[Exception]
) -> None:
    failure = error_type("Storage could not complete the operation.")
    storage = Mock(spec=Storage)
    storage.insert_if_absent.side_effect = failure

    with pytest.raises(error_type) as reported:
        create_run(storage, **run_input)

    assert reported.value is failure
