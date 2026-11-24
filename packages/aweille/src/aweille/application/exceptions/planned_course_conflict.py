from .application_error import ApplicationError


class PlannedCourseConflict(ApplicationError):
    """A committed planned course already uses this ID with different data."""
