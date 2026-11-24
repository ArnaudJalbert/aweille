from .application_error import ApplicationError


class StorageFailure(ApplicationError):
    """An unexpected storage failure prevented the operation."""
