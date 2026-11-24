from .application_error import ApplicationError


class StorageUnavailable(ApplicationError):
    """Temporary contention or unavailability; callers may retry the same ID."""
