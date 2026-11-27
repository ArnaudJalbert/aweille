"""Wired planned course commands and queries."""

from dataclasses import dataclass

from aweille.application import (
    CreatePlannedCourseCommand,
    DeletePlannedCourseCommand,
    ReadPlannedCourseQuery,
    ReadPlannedCoursesQuery,
    UpdatePlannedCourseCommand,
)


@dataclass(frozen=True, slots=True)
class PlannedCourseUseCases:
    """Planned course commands and queries, named by what they do.

    Attributes:
        create: Create a planned course, or confirm an identical retry.
        update: Edit a planned course at an expected revision.
        delete: Delete a planned course at an expected revision.
        read_one: Read one planned course.
        read_range: Read planned courses in a date range.
    """

    create: CreatePlannedCourseCommand
    update: UpdatePlannedCourseCommand
    delete: DeletePlannedCourseCommand
    read_one: ReadPlannedCourseQuery
    read_range: ReadPlannedCoursesQuery
