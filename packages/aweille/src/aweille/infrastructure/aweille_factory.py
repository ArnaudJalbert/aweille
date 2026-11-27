"""Composition root holding every wired use case, grouped by area."""

from dataclasses import dataclass

from .planned_course_use_cases import PlannedCourseUseCases


@dataclass(frozen=True, slots=True)
class AweilleFactory:
    """Every wired use case, grouped by area.

    Get one from create_factory_session, which validates the database first.

    Attributes:
        planned_courses: Planned course commands and queries.

    Example:
        with create_factory_session(database_path) as factory:
            use_case = factory.planned_courses.read_one
            output = use_case.execute(use_case.InputData(id=planned_course_id))
    """

    planned_courses: PlannedCourseUseCases
