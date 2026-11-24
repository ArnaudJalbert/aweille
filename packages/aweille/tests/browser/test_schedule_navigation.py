"""Schedule selection, calendar and real form returns through public pages."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from playwright.sync_api import Page, Route, expect
from tests.fixtures.live_server import LiveServer
from tests.fixtures.schedule import choose_date


def test_local_http_creation_and_editing_preserve_schedule_returns(
    page: Page, live_server: LiveServer
):
    # A non-loopback HTTP origin reproduces physical-phone browser restrictions.
    origin = "http://aweille.test"

    def forward_to_server(route: Route):
        route.fulfill(
            response=route.fetch(
                url=route.request.url.replace(origin, live_server.url, 1),
                headers={**route.request.headers, "host": "aweille.test"},
            )
        )

    page.route(f"{origin}/**", forward_to_server)
    page.goto(f"{origin}/?view=week&date=2026-10-21")
    assert page.evaluate("isSecureContext") is False
    add_planned_course = page.get_by_role("link", name="Add course for Wednesday")
    add_planned_course.click()
    save = page.get_by_role("button", name="Save course", exact=True)
    expect(save).to_be_enabled()
    page.get_by_role("link", name="Cancel", exact=True).click()
    expect(add_planned_course).to_be_focused()
    add_planned_course.click()
    page.get_by_label("Course type").select_option("easy")
    page.get_by_label("Distance km").fill("1")
    page.get_by_label("Pace m:ss/km").fill("6:30")
    with page.expect_response(f"{origin}/v1/planned-courses") as created:
        save.click()
    assert created.value.status == 201
    submitted = created.value.request.post_data_json
    assert submitted is not None
    planned_course_id = submitted["id"]
    assert UUID(planned_course_id).version == 4
    edit = page.get_by_role("link", name="Edit easy course on 2026-10-21")
    expect(edit).to_be_focused()
    expect(page.get_by_role("button", name="Week", exact=True)).to_have_attribute(
        "aria-pressed", "true"
    )
    edit.click()
    page.get_by_label("Personal note").fill("Saved from a local HTTP page.")
    with page.expect_response(
        f"{origin}/v1/planned-courses/{planned_course_id}"
    ) as updated:
        page.get_by_role("button", name="Save changes", exact=True).click()
    assert updated.value.status == 200
    expect(edit).to_be_focused()
    stored = page.request.get(
        f"{live_server.url}/v1/planned-courses/{planned_course_id}"
    ).json()
    assert stored["user_note"] == "Saved from a local HTTP page."
    assert stored["revision"] == "2"


@pytest.mark.parametrize("width", [320, 1280])
def test_schedule_arrows_move_by_view_and_restore_history(
    page: Page, live_server: LiveServer, width: int
):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(f"{live_server.url}/?view=day&date=2026-12-31")
    next_day = page.get_by_role("button", name="Next day", exact=True)
    expect(next_day).to_be_visible()
    expect(next_day.locator("svg")).to_be_visible()
    next_day.locator("svg").click()
    expect(page.get_by_role("region", name="Friday Jan 1")).to_be_visible()
    expect(page).to_have_url(
        f"{live_server.url}/?week=2026-12-28&view=day&date=2027-01-01"
    )
    expect(next_day).to_be_focused()
    page.get_by_role("button", name="Previous day", exact=True).click()
    expect(page.get_by_role("region", name="Thursday Dec 31")).to_be_visible()
    page.get_by_role("button", name="Week", exact=True).click()
    next_week = page.get_by_role("button", name="Next week", exact=True)
    next_week.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("region", name="Thursday Jan 7")).to_be_visible()
    expect(page).to_have_url(
        f"{live_server.url}/?week=2027-01-04&view=week&date=2027-01-07"
    )
    page.go_back()
    expect(page.get_by_role("region", name="Thursday Dec 31")).to_be_visible()
    page.get_by_role("button", name="Previous week", exact=True).click()
    expect(page.get_by_role("region", name="Thursday Dec 24")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_day_default_and_week_switch_preserve_date(page: Page, live_server: LiveServer):
    page.clock.set_fixed_time(datetime(2026, 10, 14, 12, tzinfo=UTC))
    page.goto(live_server.url)
    expect(page.get_by_role("button", name="Day", exact=True)).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(page.get_by_role("heading", level=1)).to_have_text("Today")
    expect(page.get_by_text("Training schedule", exact=True)).to_be_visible()
    expect(page.get_by_role("heading", level=2)).to_have_count(0)
    expect(page.get_by_role("region")).to_have_count(1)
    expect(page.get_by_role("link", name="Add course")).to_have_count(1)
    page.get_by_role("button", name="Week", exact=True).click()
    expect(page.get_by_role("region")).to_have_count(7)
    expect(page.get_by_role("heading", level=1)).to_have_text("This Week")
    page.get_by_role("button", name="Day", exact=True).click()
    expect(page.get_by_role("region", name="Wednesday Oct 14")).to_be_visible()
    page.reload()
    expect(page.get_by_role("region")).to_have_count(1)
    expect(page.get_by_role("region", name="Wednesday Oct 14")).to_be_visible()

    for name in ("Day", "Week"):
        selected = page.get_by_role("button", name=name, exact=True)
        selected.click()
        selected.hover()
        expect(selected).to_have_attribute("aria-pressed", "true")
        expect(selected).to_have_css("background-color", "rgb(32, 43, 40)")
        expect(selected).to_have_css("color", "rgb(250, 251, 246)")


def test_disclosures_and_cancel_restore_each_view_and_initiating_focus(
    page: Page, live_server: LiveServer, planned_course_request
):
    planned_course = {
        **planned_course_request,
        "planned_start_time": "07:30",
        "sections": [
            {"distance_m": "1000", "target_pace_seconds_per_km": "390"},
            {"distance_m": "9007199254740993123", "target_pace_seconds_per_km": "390"},
        ],
    }
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses", data=planned_course
        ).status
        == 201
    )
    page.goto(f"{live_server.url}/?view=day&date=2026-10-14")
    expect(page.get_by_text("Running", exact=True)).to_be_visible()
    assert (
        page.locator(".course-content").evaluate(
            "node => getComputedStyle(node).borderLeftWidth"
        )
        == "1px"
    )
    assert (
        page.locator(".course-content").evaluate(
            "node => getComputedStyle(node, '::before').width"
        )
        == "7px"
    )
    expect(page.get_by_role("link", name="Edit easy course")).to_contain_text(
        "9007199254740994.123 km · 2 sections · 6:30/km"
    )
    details = page.get_by_text("Hide details", exact=True)
    expect(details).to_be_visible()
    disclosure = page.locator("summary")
    expect(disclosure).to_have_accessible_name(
        "Hide details for easy course on 2026-10-14 at 07:30"
    )
    disclosure.focus()
    page.keyboard.press("Space")
    expect(page.get_by_text("Show details", exact=True)).to_be_visible()
    expect(disclosure).to_have_accessible_name(
        "Show details for easy course on 2026-10-14 at 07:30"
    )
    page.get_by_role("button", name="Week", exact=True).click()
    expect(disclosure).to_have_accessible_name(
        "Show details for easy course on 2026-10-14 at 07:30"
    )
    disclosure.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Hide details", exact=True)).to_be_visible()
    expect(disclosure).to_have_accessible_name(
        "Hide details for easy course on 2026-10-14 at 07:30"
    )
    page.get_by_role("link", name="Edit easy course").click()
    page.get_by_role("link", name="Cancel", exact=True).click()
    expect(page.get_by_role("button", name="Week", exact=True)).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(page.get_by_text("Hide details", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="Edit easy course")).to_be_focused()
    page.get_by_role("button", name="Day", exact=True).click()
    expect(page.get_by_text("Show details", exact=True)).to_be_visible()
    page.get_by_role("link", name="Add course").click()
    page.get_by_role("link", name="Cancel", exact=True).click()
    expect(page.get_by_role("link", name="Add course")).to_be_focused()
    expect(page.get_by_text("Show details", exact=True)).to_be_visible()
    choose_date(page, "2026-10-15")
    choose_date(page, "2026-10-14")
    expect(page.get_by_text("Show details", exact=True)).to_be_visible()
    page.get_by_role("button", name="Week", exact=True).click()
    expect(page.get_by_text("Hide details", exact=True)).to_be_visible()
    choose_date(page, "2026-10-21")
    choose_date(page, "2026-10-14")
    expect(page.get_by_text("Show details", exact=True)).to_be_visible()
    page.get_by_role("button", name="Day", exact=True).click()
    expect(page.get_by_text("Hide details", exact=True)).to_be_visible()
    page.reload()
    expect(page.get_by_text("Hide details", exact=True)).to_be_visible()


def test_calendar_keyboard_months_contextual_week_and_escape(
    page: Page, live_server: LiveServer
):
    page.emulate_media(forced_colors="active")
    page.goto(f"{live_server.url}/?view=day&date=2026-10-14")
    calendar = page.get_by_role("button", name="Choose date")
    calendar.click()
    expect(page.get_by_role("gridcell", name="2026-10-14")).to_be_focused()
    expect(page.get_by_role("gridcell", name="2026-10-14")).to_have_attribute(
        "aria-selected", "true"
    )
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("gridcell", name="2026-10-22")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_role("region", name="Thursday Oct 22")).to_be_visible()
    page.get_by_role("button", name="Week", exact=True).click()
    calendar.click()
    expect(page.locator('[role="gridcell"][aria-selected="true"]')).to_have_count(7)
    page.keyboard.press("ArrowLeft")
    focused = page.get_by_role("gridcell", name="2026-10-21", exact=True)
    expect(focused).to_be_focused()
    assert focused.evaluate("node => getComputedStyle(node).outlineWidth") == "3px"
    assert focused.evaluate("node => getComputedStyle(node).outlineOffset") == "3px"
    assert (
        page.get_by_role("gridcell", name="2026-10-20", exact=True).evaluate(
            "node => getComputedStyle(node).outlineStyle"
        )
        == "none"
    )
    page.get_by_role("button", name="Next month").click()
    expect(page.get_by_role("heading", name="November 2026")).to_be_visible()
    page.get_by_role("button", name="Previous month").click()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).not_to_be_visible()
    expect(calendar).to_be_focused()
    calendar.click()
    page.get_by_role("button", name="Cancel", exact=True).click()
    expect(calendar).to_be_focused()

    calendar.click()
    page.get_by_role("button", name="This Week", exact=True).click()
    expect(page.get_by_role("heading", level=1)).to_have_text("This Week")
    page.get_by_role("button", name="Day", exact=True).click()
    calendar.click()
    page.get_by_role("dialog").get_by_role("button", name="Today", exact=True).click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Today")


@pytest.mark.parametrize(
    ("view", "recovery"), [("week", "retry"), ("day", "next"), ("week", "next")]
)
def test_confirmed_cross_week_save_restores_focus_unless_navigating_elsewhere(
    page: Page, live_server: LiveServer, view: str, recovery: str
):
    page.goto(f"{live_server.url}/?view={view}&date=2026-10-14")
    page.get_by_role("link", name="Add course for Wednesday").click()
    page.get_by_label("Planned date").fill("2026-10-28")
    page.get_by_label("Course type").select_option("easy")
    page.get_by_label("Distance km").fill("1")
    page.get_by_label("Pace m:ss/km").fill("6:30")
    writes = []
    page.on(
        "request",
        lambda request: writes.append(request) if request.method == "POST" else None,
    )
    page.route(
        "**/v1/planned-courses?*",
        lambda route: route.fulfill(status=503, json={"detail": "Read failed."}),
    )
    page.get_by_role("button", name="Save course", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Read failed.")
    expect(page.get_by_role("heading", level=3)).to_have_count(0)
    page.unroute("**/v1/planned-courses?*")
    if recovery == "retry":
        page.get_by_role("button", name="Retry", exact=True).click()
        expect(
            page.get_by_role("link", name="Edit easy course on 2026-10-28")
        ).to_be_focused()
        expect(page.get_by_text("Show details", exact=True)).to_be_visible()
        expect(page).to_have_url(
            f"{live_server.url}/?week=2026-10-26&view=week&date=2026-10-28"
        )
    else:
        next_period = page.get_by_role("button", name=f"Next {view}", exact=True)
        next_period.focus()
        page.keyboard.press("Enter")
        expected_date = "2026-10-29" if view == "day" else "2026-11-04"
        expected_week = "2026-10-26" if view == "day" else "2026-11-02"
        expect(page).to_have_url(
            f"{live_server.url}/?week={expected_week}&view={view}&date={expected_date}"
        )
        expect(page.get_by_role("link", name="Add course").first).to_be_visible()
        expect(next_period).to_be_focused()
    assert len(writes) == 1


def test_content_width_controls_week_layout_and_add_targets(
    page: Page, live_server: LiveServer, planned_course_request
):
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses", data=planned_course_request
        ).status
        == 201
    )
    page.goto(f"{live_server.url}/?view=week&date=2026-10-14")
    for content_width in (559, 560):
        page.set_viewport_size({"width": content_width + 32, "height": 900})
        expect(page.get_by_role("button", name="Toggle navigation")).to_have_attribute(
            "aria-expanded", "false"
        )
        day = page.get_by_role("region", name="Wednesday Oct 14")
        header = day.locator(".day-heading").bounding_box()
        body = day.locator(".day-body").bounding_box()
        add = day.get_by_role("link", name="Add course").bounding_box()
        assert header and body and add and add["height"] >= 44
        if content_width == 559:
            assert body["y"] >= header["y"] + header["height"]
        else:
            assert body["x"] > header["x"] + header["width"]
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_form_reload_falls_back_to_heading_focus_without_reusing_context(
    page: Page, live_server: LiveServer
):
    page.goto(f"{live_server.url}/?view=week&date=2026-10-14")
    page.get_by_role("link", name="Add course for Wednesday").click()
    expect(page.get_by_role("button", name="Save course", exact=True)).to_be_enabled()
    page.reload()
    expect(page.get_by_label("Planned date")).to_have_value("2026-10-14")
    page.get_by_role("link", name="Cancel", exact=True).click()
    expect(page.get_by_role("heading", level=1)).to_be_focused()
    expect(page.get_by_role("button", name="Day", exact=True)).to_have_attribute(
        "aria-pressed", "true"
    )
