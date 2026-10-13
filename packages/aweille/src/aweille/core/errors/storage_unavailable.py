class StorageUnavailable(Exception):
    """Temporary contention or unavailability; callers may retry the same ID."""
