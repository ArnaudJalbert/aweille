from aweille.core import CourseType


def test_course_types_keep_the_agreed_api_values() -> None:
    assert {course_type.name: course_type.value for course_type in CourseType} == {
        "EASY": "easy",
        "HARD": "hard",
        "INTERVAL": "interval",
        "LONG": "long",
    }
