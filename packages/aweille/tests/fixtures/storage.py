from dataclasses import replace
from datetime import date
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from aweille.core import (
    PlannedCourse,
    PlannedCourseConflict,
    PlannedCourseNotFound,
    PlannedCourseRevisionConflict,
    PlannedCourseStorage,
)


@pytest.fixture
def storage() -> PlannedCourseStorage:
    planned_courses: dict[UUID, PlannedCourse] = {}
    deleted: set[UUID] = set()

    def save(planned_course: PlannedCourse) -> tuple[PlannedCourse, bool]:
        if planned_course.id in deleted:
            raise PlannedCourseConflict
        if planned_course.id in planned_courses:
            return planned_courses[planned_course.id], False
        planned_courses[planned_course.id] = planned_course
        return planned_course, True

    def get(start: date, end: date) -> list[PlannedCourse]:
        return list(
            reversed(
                [r for r in planned_courses.values() if start <= r.planned_date < end]
            )
        )

    def load(id: UUID) -> PlannedCourse | None:
        return planned_courses.get(id)

    def replace_planned_course(
        planned_course: PlannedCourse, *, expected_revision: int
    ) -> PlannedCourse:
        current = planned_courses.get(planned_course.id)
        if current is None:
            raise PlannedCourseNotFound
        if current.revision != expected_revision:
            raise PlannedCourseRevisionConflict
        if current.to_dict() | {"revision": "1"} != planned_course.to_dict() | {
            "revision": "1"
        }:
            current = replace(planned_course, revision=current.revision + 1)
            planned_courses[planned_course.id] = current
        return current

    def delete(id: UUID, *, expected_revision: int) -> None:
        current = planned_courses.get(id)
        if current is None:
            raise PlannedCourseNotFound
        if current.revision != expected_revision:
            raise PlannedCourseRevisionConflict
        del planned_courses[id]
        deleted.add(id)

    return cast(
        PlannedCourseStorage,
        SimpleNamespace(
            save=save, get=get, load=load, replace=replace_planned_course, delete=delete
        ),
    )
