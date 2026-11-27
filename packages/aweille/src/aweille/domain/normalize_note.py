def normalize_note(note: str | None) -> str | None:
    """Trim a plain-text note, treating a blank note as absent.

    Args:
        note: Note text, or None when absent. Other values pass through for the
            planned course to reject.

    Returns:
        The note without outer whitespace, or None when it is absent or blank.
    """
    return note.strip() or None if isinstance(note, str) else note
