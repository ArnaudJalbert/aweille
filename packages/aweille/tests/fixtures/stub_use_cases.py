"""Provide autospec planned course use cases for HTTP tests."""

from unittest.mock import create_autospec

import pytest
from aweille.application import (
    CreatePlannedCourseCommand,
    DeletePlannedCourseCommand,
    ReadPlannedCourseQuery,
    ReadPlannedCoursesQuery,
    UpdatePlannedCourseCommand,
)
from aweille.infrastructure import PlannedCourseUseCases


@pytest.fixture
def stub_use_cases() -> PlannedCourseUseCases:
    """Provide planned course use cases as autospec mocks that do nothing."""
    return PlannedCourseUseCases(
        create=create_autospec(CreatePlannedCourseCommand, instance=True),
        update=create_autospec(UpdatePlannedCourseCommand, instance=True),
        delete=create_autospec(DeletePlannedCourseCommand, instance=True),
        read_one=create_autospec(ReadPlannedCourseQuery, instance=True),
        read_range=create_autospec(ReadPlannedCoursesQuery, instance=True),
    )
