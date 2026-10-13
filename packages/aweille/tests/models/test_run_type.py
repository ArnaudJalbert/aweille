from aweille.core import RunType


def test_run_types_keep_the_agreed_api_values() -> None:
    assert {run_type.name: run_type.value for run_type in RunType} == {
        "EASY": "easy",
        "HARD": "hard",
        "INTERVAL": "interval",
        "LONG": "long",
    }
