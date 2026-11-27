"""Serve the HTTP app over autospec use cases for failure and transport tests."""

from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import create_autospec

import pytest
from aweille.api.create_app import create_app
from aweille.application import (
    CreatePlannedCourseCommand,
    DeletePlannedCourseCommand,
    ReadPlannedCourseQuery,
    ReadPlannedCoursesQuery,
    UpdatePlannedCourseCommand,
)
from aweille.infrastructure import AweilleFactory, PlannedCourseUseCases
from fastapi.testclient import TestClient


@pytest.fixture
def stub_use_cases() -> PlannedCourseUseCases:
    return PlannedCourseUseCases(
        create=create_autospec(CreatePlannedCourseCommand, instance=True),
        update=create_autospec(UpdatePlannedCourseCommand, instance=True),
        delete=create_autospec(DeletePlannedCourseCommand, instance=True),
        read_one=create_autospec(ReadPlannedCourseQuery, instance=True),
        read_range=create_autospec(ReadPlannedCoursesQuery, instance=True),
    )


@pytest.fixture
def stub_client(stub_use_cases: PlannedCourseUseCases):
    @contextmanager
    def open_stub_factory() -> Generator[AweilleFactory]:
        yield AweilleFactory(planned_courses=stub_use_cases)

    with TestClient(
        create_app(factory=open_stub_factory), raise_server_exceptions=False
    ) as client:
        yield client
