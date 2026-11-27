from datetime import time


def normalize_start_time(value: time | None) -> time | None:
    """Clear the daylight-saving occurrence a local start time may select.

    Args:
        value: Local start time, or None when absent. Other values pass through
            for the planned course to reject.

    Returns:
        The same clock time without a selected occurrence, or None.
    """
    return value.replace(fold=0) if type(value) is time else value
