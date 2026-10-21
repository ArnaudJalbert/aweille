"""Public schedule interactions reused by browser contract scenarios."""

from playwright.sync_api import Page


def choose_date(page: Page, value: str) -> None:
    """Select a calendar date through the contextual picker.

    Args:
        page: The open schedule page.
        value: An ISO calendar date visible in the contextual picker.
    """
    page.get_by_role("button", name="Choose date", exact=True).click()
    page.get_by_role("gridcell", name=value, exact=True).click()
