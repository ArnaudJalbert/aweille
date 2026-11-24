from .application_error import ApplicationError


class PlannedCourseRevisionConflict(ApplicationError):
    """The expected revision is no longer current."""
