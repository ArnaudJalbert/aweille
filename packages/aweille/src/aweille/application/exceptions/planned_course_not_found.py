from .application_error import ApplicationError


class PlannedCourseNotFound(ApplicationError):
    """The planned course no longer exists."""
