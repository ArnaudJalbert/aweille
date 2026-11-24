"""Provide the installed database setup command for Aweille."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

from .validate_database import SCHEMA_VERSION


def create_database(path: str | Path) -> None:
    """Create the initial schema in a new file without touching existing storage.

    Args:
        path: New database file, with an existing parent directory.

    Raises:
        FileExistsError: The path already exists and must remain unchanged.
        OSError: The file cannot be created.
        sqlite3.Error: Schema creation fails; the new file is removed.
    """
    path = Path(path)
    with path.open("xb"):
        pass
    try:
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "CREATE TABLE planned_courses ("
                "id TEXT NOT NULL PRIMARY KEY, planned_date TEXT NOT NULL, "
                "planned_start_time TEXT, course_type TEXT NOT NULL, "
                "sections TEXT NOT NULL, user_note TEXT, trainer_note TEXT, "
                "revision TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE INDEX planned_courses_planned_date "
                "ON planned_courses(planned_date)"
            )
            connection.execute(
                "CREATE TABLE deleted_planned_course_ids (id TEXT NOT NULL PRIMARY KEY)"
            )
            connection.execute("PRAGMA application_id = 0x41574549")
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    except BaseException:
        path.unlink()
        raise


def main() -> None:
    """Create a database at the required command-line path.

    Raises:
        SystemExit: Arguments are invalid, creation fails, or storage exists.
    """
    parser = argparse.ArgumentParser(
        description="Create a new Aweille SQLite database."
    )
    parser.add_argument(
        "path", type=Path, help="New database file; its parent must exist."
    )
    args = parser.parse_args()
    try:
        create_database(args.path)
    except FileExistsError:
        parser.exit(1, "Database already exists; no changes made.\n")
    except (OSError, sqlite3.Error):
        parser.exit(1, "Database creation failed.\n")


if __name__ == "__main__":
    main()
