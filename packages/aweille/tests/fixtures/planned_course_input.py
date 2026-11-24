from datetime import date
from typing import Any
from uuid import UUID

import pytest
from aweille.domain import CourseType, Distance, Pace, Section


@pytest.fixture
def planned_course_input() -> dict[str, Any]:
    return {
        "id": UUID("54D97D4D-FADB-4D50-926E-AF1BB26C711A"),
        "planned_date": date(2026, 10, 14),
        "course_type": CourseType.INTERVAL,
        "sections": [
            Section(Distance(1000), Pace(390)),
            Section(Distance(1000), Pace(345)),
            Section(Distance(1000), Pace(390)),
        ],
        "user_note": "  Keep the first section easy.  ",
        "trainer_note": "  Finish relaxed.  ",
    }
