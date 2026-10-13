from dataclasses import replace
from datetime import date, time
from typing import Any

import pytest
from aweille.core import (
    Distance,
    Pace,
    PlannedRun,
    RunStorage,
    Section,
    ValidationError,
    create_run,
)


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"id": "invalid"}, "id"),
        ({"run_type": "easy"}, "run_type"),
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
def test_planned_run_constructor_rejects_invalid_or_unnormalized_fields(
    storage: RunStorage,
    run_input: dict[str, Any],
    changes: dict[str, Any],
    field: str,
) -> None:
    run, _ = create_run(storage, **run_input)

    with pytest.raises(ValidationError) as failure:
        replace(run, **changes)

    assert failure.value.problems[0].loc == (field,)


def test_planned_run_dictionary_round_trip_preserves_exact_ordered_targets(
    storage: RunStorage, run_input: dict[str, Any]
) -> None:
    section = Section(Distance(10**5003), Pace(10**5000))
    run_input["sections"] = [section, Section(Distance(1000), Pace(345)), section]
    run, _ = create_run(storage, **run_input, planned_start_time=time(7, 30))
    huge = {
        "distance_m": "1" + "0" * 5003,
        "target_pace_seconds_per_km": "1" + "0" * 5000,
    }
    expected = {
        "id": "54d97d4d-fadb-4d50-926e-af1bb26c711a",
        "planned_date": "2026-10-14",
        "planned_start_time": "07:30",
        "run_type": "interval",
        "sections": [
            huge,
            {"distance_m": "1000", "target_pace_seconds_per_km": "345"},
            huge,
        ],
        "user_note": "Keep the first section easy.",
        "trainer_note": "Finish relaxed.",
    }

    assert run.to_dict() == expected
    assert PlannedRun.from_dict(expected) == run


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
        {"run_type": "PRIVATE"},
        {"user_note": "  PRIVATE  "},
        {"planned_date": "2026-03-08", "planned_start_time": "02:30"},
    ],
)
def test_dictionary_decoder_rejects_malformed_or_noncanonical_values(
    storage: RunStorage, run_input: dict[str, Any], changes: dict[str, Any]
) -> None:
    run, _ = create_run(storage, **run_input)
    data = run.to_dict()
    data.update(changes)

    with pytest.raises(ValueError) as failure:
        PlannedRun.from_dict(data)

    assert "PRIVATE" not in str(failure.value)


def test_dictionary_decoder_preserves_domain_validation_details(
    storage: RunStorage, run_input: dict[str, Any]
) -> None:
    run, _ = create_run(storage, **run_input)
    data = run.to_dict()
    data["sections"][0]["distance_m"] = "0"

    with pytest.raises(ValidationError) as failure:
        PlannedRun.from_dict(data)

    assert failure.value.problems[0].code == "invalid_distance"
