"""Weekly-view contracts observed through the browser and HTTP API."""

import re
from datetime import UTC, datetime

import pytest
from playwright.sync_api import Browser, Page, Route, expect
from tests.fixtures.live_server import LiveServer
from tests.fixtures.schedule import choose_date


def test_api_created_planned_course_is_displayed_after_real_restart(
    page: Page, live_server: LiveServer, planned_course_request
):
    representative = {
        **planned_course_request,
        "course_type": "interval",
        "planned_start_time": "07:30",
        "sections": [
            {"distance_m": "1000", "target_pace_seconds_per_km": pace}
            for pace in ("390", "345", "390")
        ],
        "user_note": "Keep the first section easy.",
        "trainer_note": "Finish relaxed.",
    }
    saved = page.request.post(
        f"{live_server.url}/v1/planned-courses", data=representative
    )
    assert saved.status == 201
    week_url = f"{live_server.url}/?week=2026-10-12&view=week"
    read_url = f"{live_server.url}/v1/planned-courses?start=2026-10-12&end=2026-10-19"
    assert page.request.get(read_url).json() == [saved.json()]

    page.goto(week_url)
    expect(page.locator("#exact-date")).to_have_text("October 12 to 18, 2026")
    expect(page.get_by_role("region")).to_have_count(7)
    wednesday = page.get_by_role("region", name="Wednesday Oct 14")
    expect(wednesday.get_by_role("heading", level=3)).to_have_text("Interval course")
    expect(wednesday.get_by_role("link", name="Edit interval course")).to_contain_text(
        "3 km · 3 sections · Varied pace"
    )
    for summary in wednesday.locator("summary").all():
        summary.click()
    expect(wednesday.get_by_role("listitem")).to_have_text(
        ["1 km6:30/km", "1 km5:45/km", "1 km6:30/km"]
    )
    expect(wednesday.get_by_text("Personal note", exact=True)).to_be_visible()
    expect(wednesday.get_by_text("Keep the first section easy.")).to_be_visible()
    expect(wednesday.get_by_text("Trainer note", exact=True)).to_be_visible()
    expect(wednesday.get_by_text("Finish relaxed.")).to_be_visible()
    expect(page.get_by_text("No courses planned", exact=True)).to_have_count(6)
    expect(page.get_by_role("link", name="Add course")).to_have_count(7)

    live_server.restart()
    assert page.request.get(read_url).json() == [saved.json()]
    page.reload()
    expect(wednesday.get_by_role("heading", level=3)).to_have_text("Interval course")
    replay = page.request.post(
        f"{live_server.url}/v1/planned-courses", data=representative
    )
    assert replay.status == 200
    assert page.request.get(read_url).json() == [saved.json()]
    page.reload()
    expect(page.get_by_role("heading", level=3)).to_have_count(1)


@pytest.mark.browser_context_args(timezone_id="Asia/Tokyo")
def test_montreal_week_navigation_history_and_open_tab_rollover(
    page: Page, live_server: LiveServer
):
    page.clock.set_fixed_time(datetime(2026, 1, 5, 4, 30, tzinfo=UTC))
    page.goto(live_server.url)
    expect(page).to_have_url(
        f"{live_server.url}/?week=2025-12-29&view=day&date=2026-01-04"
    )
    expect(page.get_by_role("heading", level=1)).to_have_text("Today")
    page.get_by_role("button", name="Week", exact=True).click()
    expect(page.locator("#exact-date")).to_have_text(
        "December 29, 2025 to January 4, 2026"
    )
    choose_date(page, "2026-01-12")
    expect(page.get_by_role("heading", level=1)).to_have_text("In 2 Weeks")
    page.go_back()
    expect(page.get_by_role("heading", level=1)).to_have_text("This Week")
    page.go_forward()
    page.reload()
    expect(page.get_by_role("heading", level=1)).to_have_text("In 2 Weeks")
    page.clock.set_fixed_time(datetime(2026, 1, 5, 5, 30, tzinfo=UTC))
    page.get_by_role("button", name="Today", exact=True).click()
    expect(page).to_have_url(
        f"{live_server.url}/?week=2026-01-05&view=day&date=2026-01-05"
    )
    expect(page.get_by_role("region")).to_have_count(1)

    # Montreal's DST change still uses calendar weeks and the new UTC-4 midnight.
    page.clock.set_fixed_time(datetime(2026, 3, 8, 6, 30, tzinfo=UTC))
    page.get_by_role("button", name="Today", exact=True).click()
    page.get_by_role("button", name="Week", exact=True).click()
    expect(page.locator("#exact-date")).to_have_text("March 2 to 8, 2026")
    choose_date(page, "2026-03-09")
    expect(page.get_by_role("heading", level=1)).to_have_text("Next Week")
    page.clock.set_fixed_time(datetime(2026, 3, 9, 4, 30, tzinfo=UTC))
    page.get_by_role("button", name="Today", exact=True).click()
    expect(page).to_have_url(
        f"{live_server.url}/?week=2026-03-09&view=day&date=2026-03-09"
    )


def test_non_monday_selection_normalizes_the_url_and_reads_its_full_week(
    page: Page, live_server: LiveServer
):
    with page.expect_request(
        f"{live_server.url}/v1/planned-courses?start=2026-01-26&end=2026-02-02"
    ):
        page.goto(f"{live_server.url}/?week=2026-02-01&view=week")
    expect(page).to_have_url(re.compile(r"/\?week=2026-01-26(?:&.*)?$"))
    expect(page.locator("#exact-date")).to_have_text("January 26 to February 1, 2026")
    expect(page.get_by_text("No courses planned", exact=True)).to_have_count(7)


@pytest.mark.parametrize("selection", ["not-a-date", "2026-02-30", "9999-12-31"])
def test_invalid_week_does_not_guess_a_range_and_can_recover(
    page: Page, live_server: LiveServer, selection: str
):
    reads = []
    page.on(
        "request",
        lambda request: (
            reads.append(request.url) if "/v1/planned-courses?" in request.url else None
        ),
    )
    page.clock.set_fixed_time(datetime(2026, 10, 14, 12, tzinfo=UTC))
    page.goto(f"{live_server.url}/?week={selection}&view=week")
    expect(page.get_by_role("alert")).to_contain_text("Invalid week selection")
    assert reads == []
    expect(page.get_by_text("No courses planned", exact=True)).to_have_count(0)
    expect(page.get_by_role("button", name="Choose date")).to_be_enabled()
    expect(
        page.get_by_role("button", name=re.compile(r"^Previous (day|week)$"))
    ).to_be_disabled()
    expect(
        page.get_by_role("button", name=re.compile(r"^Next (day|week)$"))
    ).to_be_disabled()
    page.get_by_role("button", name="Today", exact=True).click()
    expect(page).to_have_url(re.compile(r"/\?week=2026-10-12(?:&.*)?$"))
    expect(page.get_by_text("No courses planned", exact=True)).to_have_count(1)


@pytest.mark.parametrize(
    ("failure", "explanation"),
    [
        ("network", "Check your connection"),
        (503, "Course storage is temporarily unavailable."),
        (500, "Unable to read courses."),
    ],
)
def test_read_failure_keeps_navigation_and_retry_reads_the_selected_week(
    page: Page, live_server: LiveServer, failure, explanation: str
):
    def fail_read(route: Route):
        if failure == "network":
            route.abort("failed")
        else:
            route.fulfill(status=failure, json={"detail": explanation})

    page.route("**/v1/planned-courses?*", fail_read)
    page.goto(f"{live_server.url}/?week=2026-10-12&view=week")
    expect(page.get_by_role("alert")).to_contain_text(
        "Could not load courses for this week"
    )
    expect(page.get_by_role("alert")).to_contain_text(explanation)
    expect(page.get_by_text("No courses planned", exact=True)).to_have_count(0)
    choose_date(page, "2026-10-19")
    expect(page).to_have_url(re.compile(r"/\?week=2026-10-19(?:&.*)?$"))
    expect(page.get_by_role("alert")).to_contain_text(explanation)

    page.unroute("**/v1/planned-courses?*", fail_read)
    with page.expect_request(
        f"{live_server.url}/v1/planned-courses?start=2026-10-19&end=2026-10-26"
    ):
        page.get_by_role("button", name="Retry", exact=True).click()
    expect(page.get_by_text("No courses planned", exact=True)).to_have_count(7)
    expect(page.get_by_role("alert")).to_have_count(0)
    expect(page).to_have_url(re.compile(r"/\?week=2026-10-19(?:&.*)?$"))


@pytest.mark.parametrize("stale_failure", [False, True])
def test_loading_hides_old_courses_and_late_reads_cannot_replace_the_latest_week(
    page: Page, live_server: LiveServer, planned_course_request, stale_failure: bool
):
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses", data=planned_course_request
        ).status
        == 201
    )
    next_planned_course = {
        **planned_course_request,
        "id": "694f488d-2cc2-4c3f-a7cd-60ad0307295f",
        "planned_date": "2026-10-28",
        "course_type": "long",
    }
    saved = page.request.post(
        f"{live_server.url}/v1/planned-courses", data=next_planned_course
    )
    assert saved.status == 201
    page.goto(f"{live_server.url}/?week=2026-10-12&view=week")
    expect(page.get_by_role("heading", level=3)).to_have_text("Easy course")
    held: list[Route] = []
    page.route("**/v1/planned-courses?*", lambda route: held.append(route))

    with page.expect_request("**/v1/planned-courses?start=2026-10-19&end=2026-10-26"):
        choose_date(page, "2026-10-19")
    expect(page.get_by_role("status")).to_have_text("Loading courses...")
    expect(page.locator("#exact-date")).to_have_text("October 19 to 25, 2026")
    expect(page.get_by_role("heading", level=3)).to_have_count(0)
    expect(page.get_by_text("No courses planned", exact=True)).to_have_count(0)
    with page.expect_request("**/v1/planned-courses?start=2026-10-26&end=2026-11-02"):
        choose_date(page, "2026-10-26")
    assert len(held) == 2
    held[1].fulfill(json=[saved.json()])
    wednesday = page.get_by_role("region", name="Wednesday Oct 28")
    expect(wednesday.get_by_role("heading", level=3)).to_have_text("Long course")

    with page.expect_response("**/v1/planned-courses?start=2026-10-19&end=2026-10-26"):
        if stale_failure:
            held[0].fulfill(status=503, json={"detail": "Old read failed."})
        else:
            held[0].fulfill(json=[])
    # A following browser round trip lets the delivered response's handlers run.
    page.get_by_role("button", name="Today", exact=True).focus()
    expect(page).to_have_url(re.compile(r"/\?week=2026-10-26(?:&.*)?$"))
    expect(wednesday.get_by_role("heading", level=3)).to_have_text("Long course")
    expect(page.get_by_role("alert")).to_have_count(0)
    expect(page.get_by_role("status")).not_to_be_visible()


def test_untimed_planned_courses_exact_numbers_plain_text_notes_and_phone_layout(
    page: Page, live_server: LiveServer, planned_course_request
):
    note = '<img src=x onerror="document.body.dataset.injected=1">\n' + "A" * 180
    variants = [
        {
            "id": "cf865c08-4f90-4a99-aeab-3b6bf57f47e6",
            "course_type": "easy",
            "user_note": note,
            "sections": [{"distance_m": "1", "target_pace_seconds_per_km": "1"}],
        },
        {
            "id": "3bb59821-4d85-4b58-8a83-4fc96f3ba4c4",
            "course_type": "hard",
            "planned_start_time": "07:30",
            "sections": [{"distance_m": "1010", "target_pace_seconds_per_km": "60"}],
        },
        {
            "id": "b58db6e7-5d9b-4e35-8129-7ca1f88239fc",
            "course_type": "long",
            "planned_start_time": "12:00",
            "sections": [
                {
                    "distance_m": "9007199254740993123",
                    "target_pace_seconds_per_km": "9007199254740993123",
                },
                {"distance_m": "9" * 120, "target_pace_seconds_per_km": "390"},
            ],
        },
    ]
    for variant in variants:
        assert (
            page.request.post(
                f"{live_server.url}/v1/planned-courses",
                data={**planned_course_request, **variant},
            ).status
            == 201
        )

    page.set_viewport_size({"width": 320, "height": 640})
    page.goto(f"{live_server.url}/?week=2026-10-12&view=week")
    wednesday = page.get_by_role("region", name="Wednesday Oct 14")
    expect(wednesday.get_by_role("heading", level=3)).to_have_text(
        ["Hard course", "Long course", "Easy course"]
    )
    for summary in wednesday.locator("summary").all():
        summary.click()
    expect(wednesday.get_by_role("listitem")).to_have_text(
        [
            "1.01 km1:00/km",
            "9007199254740993.123 km150119987579016552:03/km",
            f"{'9' * 117}.999 km6:30/km",
            "0.001 km0:01/km",
        ]
    )
    expect(wednesday.get_by_text(note, exact=True)).to_be_visible()
    assert wednesday.get_by_text(note, exact=True).text_content() == note
    assert (
        wednesday.get_by_text(note, exact=True).evaluate(
            "node => getComputedStyle(node).whiteSpace"
        )
        == "pre-wrap"
    )
    expect(page.get_by_role("img")).to_have_count(0)
    assert page.locator("body").get_attribute("data-injected") is None
    expect(wednesday.get_by_text("Trainer note", exact=True)).to_have_count(0)
    assert (
        wednesday.get_by_text("Untimed", exact=True).evaluate(
            "node => getComputedStyle(node).fontSize"
        )
        == "14px"
    )
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    expect(page.get_by_text("Aweille", exact=True)).not_to_be_visible()
    expect(page.get_by_role("button", name="Toggle navigation")).to_be_visible()


@pytest.mark.parametrize("javascript_enabled", [False, True])
def test_javascript_disabled_or_missing_explains_why_planned_courses_cannot_load(
    browser: Browser, live_server: LiveServer, javascript_enabled: bool
):
    with browser.new_context(java_script_enabled=javascript_enabled) as context:
        page = context.new_page()
        if javascript_enabled:
            page.route("**/static/weekly.js", lambda route: route.abort())
        page.goto(live_server.url)
        expect(page.get_by_role("status")).to_have_text(
            "JavaScript is required to load your courses."
        )
        expect(page.get_by_text("No courses planned", exact=True)).to_have_count(0)
        expect(page.get_by_role("link", name="Add course")).to_have_count(0)
        expect(page.get_by_role("button", name="Save course")).to_have_count(0)


def test_keyboard_navigation_and_retry_keep_visible_focus(
    page: Page, live_server: LiveServer
):
    page.clock.set_fixed_time(datetime(2026, 10, 14, 12, tzinfo=UTC))
    page.goto(live_server.url)
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Collapse navigation")).to_be_focused()
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Schedule", exact=True)).to_be_focused()
    page.get_by_role("button", name="Toggle navigation").focus()
    page.keyboard.press("Tab")
    day = page.get_by_role("button", name="Day", exact=True)
    expect(day).to_be_focused()
    assert day.evaluate("node => getComputedStyle(node).outlineWidth") == "3px"
    page.keyboard.press("Tab")
    week = page.get_by_role("button", name="Week", exact=True)
    expect(week).to_be_focused()
    assert week.evaluate("node => getComputedStyle(node).outlineWidth") == "3px"
    page.keyboard.press("Enter")
    expect(page.get_by_role("region")).to_have_count(7)
    page.route(
        "**/v1/planned-courses?*",
        lambda route: route.fulfill(status=503, json={"detail": "Try again later."}),
    )
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Today", exact=True)).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_role("alert")).to_contain_text("Try again later.")
    page.get_by_role("button", name="Retry", exact=True).focus()
    page.unroute("**/v1/planned-courses?*")
    page.keyboard.press("Enter")
    expect(page.get_by_text("No courses planned", exact=True)).to_have_count(1)
    expect(page.get_by_role("heading", level=1)).to_be_focused()


@pytest.mark.parametrize("selection", ["0001-01-01", "9999-12-20"])
def test_calendar_limits_allow_complete_api_ranges(
    page: Page, live_server: LiveServer, selection: str
):
    page.goto(f"{live_server.url}/?week={selection}&view=week")
    expect(page.get_by_text("No courses planned", exact=True)).to_have_count(7)
    boundary = "Previous week" if selection.startswith("0001") else "Next week"
    expect(page.get_by_role("button", name=boundary, exact=True)).to_be_disabled()
    page.get_by_role("button", name="Choose date").click()
    if selection.startswith("0001"):
        expect(page.get_by_role("button", name="Previous month")).to_be_disabled()
    else:
        expect(page.get_by_role("button", name="Next month")).to_be_disabled()
        expect(page.get_by_role("gridcell", name="9999-12-31")).to_be_disabled()
    expect(page.get_by_role("button", name="Cancel", exact=True)).to_be_enabled()
    page.get_by_role("button", name="Cancel", exact=True).click()
    if selection.startswith("0001"):
        page.get_by_role("button", name="Day", exact=True).click()
        expect(page.get_by_role("button", name="Previous day")).to_be_disabled()
    else:
        page.goto(f"{live_server.url}/?view=day&date=9999-12-26")
        expect(page.get_by_role("button", name="Next day")).to_be_disabled()


def test_returning_to_invalid_selection_ignores_an_outstanding_read(
    page: Page, live_server: LiveServer
):
    page.goto(f"{live_server.url}/?week=invalid&view=week")
    expect(page.get_by_role("alert")).to_contain_text("Invalid week selection")
    held: list[Route] = []
    page.route("**/v1/planned-courses?*", lambda route: held.append(route))
    with page.expect_request("**/v1/planned-courses?*"):
        page.get_by_role("button", name="Today", exact=True).click()
    expect(page.get_by_role("status")).to_have_text("Loading courses...")
    page.go_back()
    expect(page.get_by_role("alert")).to_contain_text("Invalid week selection")
    with page.expect_response("**/v1/planned-courses?*"):
        held[0].fulfill(json=[])
    page.get_by_role("button", name="Today", exact=True).focus()
    expect(page).to_have_url(re.compile(r"/\?week=invalid(?:&.*)?$"))
    expect(page.get_by_role("alert")).to_contain_text("Invalid week selection")
    expect(page.get_by_text("No courses planned", exact=True)).to_have_count(0)
