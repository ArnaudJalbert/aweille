from dataclasses import replace
from datetime import date, time
from typing import Any

import pytest
from aweille.core import (
    Distance,
    Pace,
    PlannedCourse,
    PlannedCourseStorage,
    Section,
    ValidationError,
    create_planned_course,
)


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"id": "invalid"}, "id"),
        ({"course_type": "easy"}, "course_type"),
        ({"sections": []}, "sections"),
        ({"sections": [Section(Distance(1000), Pace(390))]}, "sections"),
        ({"user_note": 123}, "user_note"),
        ({"user_note": "  Needs trimming  "}, "user_note"),
        ({"trainer_note": True}, "trainer_note"),
        ({"trainer_note": ""}, "trainer_note"),
        (
            {
                "planned_date": date(2026, 11, 1),
                "planned_start_time": time(1, 30, fold=1),
            },
            "planned_start_time",
        ),
        (
            {
                "planned_date": date(2026, 11, 1),
                "planned_start_time": time(1, 30, 1),
            },
            "planned_start_time",
        ),
    ],
)
def test_planned_course_constructor_rejects_invalid_or_unnormalized_fields(
    storage: PlannedCourseStorage,
    planned_course_input: dict[str, Any],
    changes: dict[str, Any],
    field: str,
) -> None:
    planned_course, _ = create_planned_course(storage, **planned_course_input)

    with pytest.raises(ValidationError) as failure:
        replace(planned_course, **changes)

    assert failure.value.problems[0].loc == (field,)


def test_planned_course_dictionary_round_trip_preserves_exact_ordered_targets(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    section = Section(Distance(10**5003), Pace(10**5000))
    planned_course_input["sections"] = [
        section,
        Section(Distance(1000), Pace(345)),
        section,
    ]
    planned_course, _ = create_planned_course(
        storage, **planned_course_input, planned_start_time=time(7, 30)
    )
    huge = {
        "distance_m": "1" + "0" * 5003,
        "target_pace_seconds_per_km": "1" + "0" * 5000,
    }
    expected = {
        "id": "54d97d4d-fadb-4d50-926e-af1bb26c711a",
        "planned_date": "2026-10-14",
        "planned_start_time": "07:30",
        "course_type": "interval",
        "sections": [
            huge,
            {"distance_m": "1000", "target_pace_seconds_per_km": "345"},
            huge,
        ],
        "user_note": "Keep the first section easy.",
        "trainer_note": "Finish relaxed.",
        "revision": "1",
    }

    assert planned_course.to_dict() == expected
    assert PlannedCourse.from_dict(expected) == planned_course


@pytest.mark.parametrize(
    "changes",
    [
        {"PRIVATE": "unexpected field"},
        {"sections": {"distance_m": "1000", "target_pace_seconds_per_km": "390"}},
        {
            "sections": [
                {
                    "distance_m": "1000",
                    "target_pace_seconds_per_km": "390",
                    "PRIVATE": True,
                }
            ]
        },
        {"sections": [{"distance_m": 1000, "target_pace_seconds_per_km": "390"}]},
        {"sections": [{"distance_m": "1e3", "target_pace_seconds_per_km": "390"}]},
        {"sections": [{"distance_m": "01000", "target_pace_seconds_per_km": "390"}]},
        {"sections": []},
        {"id": "54D97D4D-FADB-4D50-926E-AF1BB26C711A"},
        {"course_type": "PRIVATE"},
        {"user_note": "  PRIVATE  "},
        {"planned_date": "2026-03-08", "planned_start_time": "02:30"},
    ],
)
def test_dictionary_decoder_rejects_malformed_or_noncanonical_values(
    storage: PlannedCourseStorage,
    planned_course_input: dict[str, Any],
    changes: dict[str, Any],
) -> None:
    planned_course, _ = create_planned_course(storage, **planned_course_input)
    data = planned_course.to_dict()
    data.update(changes)

    with pytest.raises(ValueError) as failure:
        PlannedCourse.from_dict(data)

    assert "PRIVATE" not in str(failure.value)


def test_dictionary_decoder_preserves_domain_validation_details(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    planned_course, _ = create_planned_course(storage, **planned_course_input)
    data = planned_course.to_dict()
    data["sections"][0]["distance_m"] = "0"

    with pytest.raises(ValidationError) as failure:
        PlannedCourse.from_dict(data)

    assert failure.value.problems[0].code == "invalid_distance"
