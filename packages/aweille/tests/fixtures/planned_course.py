from datetime import date
from uuid import UUID

import pytest
from aweille.domain import CourseType, Distance, Pace, PlannedCourse, Section


@pytest.fixture
def planned_course() -> PlannedCourse:
    return PlannedCourse(
        id=UUID("54d97d4d-fadb-4d50-926e-af1bb26c711a"),
        planned_date=date(2026, 10, 14),
        planned_start_time=None,
        course_type=CourseType.INTERVAL,
        sections=(
            Section(Distance(1000), Pace(390)),
            Section(Distance(1000), Pace(345)),
            Section(Distance(1000), Pace(390)),
        ),
        user_note="Keep the first section easy.",
        trainer_note="Finish relaxed.",
    )
