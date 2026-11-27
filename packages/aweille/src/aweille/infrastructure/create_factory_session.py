"""Open a factory session over a validated SQLite database."""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from aweille.application import (
    CreatePlannedCourseCommand,
    DeletePlannedCourseCommand,
    ReadPlannedCourseQuery,
    ReadPlannedCoursesQuery,
    UpdatePlannedCourseCommand,
)
from aweille.interface_adapters import (
    SQLitePlannedCourseReader,
    SQLitePlannedCourseRepository,
    validate_database_file,
)

from .aweille_factory import AweilleFactory
from .planned_course_use_cases import PlannedCourseUseCases


@contextmanager
def create_factory_session(database_path: Path) -> Generator[AweilleFactory]:
    """Validate the database, then yield a factory of wired use cases.

    The session holds no open connection. Each operation opens its own.

    Args:
        database_path: Absolute path to an existing Aweille database file.

    Yields:
        A factory whose use cases read and write the database.

    Raises:
        StorageFailure: The database is incompatible or holds invalid data.
            Nothing is built.

    Example:
        with create_factory_session(database_path) as factory:
            use_case = factory.planned_courses.read_one
            output = use_case.execute(use_case.InputData(id=planned_course_id))
    """
    validate_database_file(database_path)
    yield AweilleFactory(planned_courses=_build_planned_courses(database_path))


def _build_planned_courses(database_path: Path) -> PlannedCourseUseCases:
    repository = SQLitePlannedCourseRepository(database_path)
    reader = SQLitePlannedCourseReader(database_path)
    return PlannedCourseUseCases(
        create=CreatePlannedCourseCommand(repository),
        update=UpdatePlannedCourseCommand(repository),
        delete=DeletePlannedCourseCommand(repository),
        read_one=ReadPlannedCourseQuery(reader),
        read_range=ReadPlannedCoursesQuery(reader),
    )
