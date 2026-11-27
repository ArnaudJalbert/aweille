"""Serve the HTTP app over stub use cases for failure and transport tests."""

from collections.abc import Generator
from contextlib import contextmanager

import pytest
from aweille.api.create_app import create_app
from aweille.infrastructure import AweilleFactory, PlannedCourseUseCases
from fastapi.testclient import TestClient


@pytest.fixture
def stub_client(stub_use_cases: PlannedCourseUseCases) -> Generator[TestClient]:
    """Serve the HTTP app over the stub use cases, returning 500s instead of raising."""

    @contextmanager
    def open_stub_factory() -> Generator[AweilleFactory]:
        yield AweilleFactory(planned_courses=stub_use_cases)

    with TestClient(
        create_app(factory=open_stub_factory), raise_server_exceptions=False
    ) as client:
        yield client
