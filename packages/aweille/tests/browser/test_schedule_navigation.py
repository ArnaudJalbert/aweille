"""Schedule selection, calendar and real form returns through public pages."""

from datetime import UTC, datetime

from playwright.sync_api import Page, expect
from tests.fixtures.live_server import LiveServer
from tests.fixtures.schedule import choose_date


def test_day_default_and_week_switch_preserve_date(page: Page, live_server: LiveServer):
    page.clock.set_fixed_time(datetime(2026, 10, 14, 12, tzinfo=UTC))
    page.goto(live_server.url)
    expect(page.get_by_role("button", name="Day", exact=True)).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(page.get_by_role("heading", level=1)).to_have_text("Today")
    expect(page.get_by_role("region")).to_have_count(1)
    expect(page.get_by_role("link", name="Add run")).to_have_count(1)
    page.get_by_role("button", name="Week", exact=True).click()
    expect(page.get_by_role("region")).to_have_count(7)
    expect(page.get_by_role("heading", level=1)).to_have_text("This Week")
    page.get_by_role("button", name="Day", exact=True).click()
    expect(page.get_by_role("region", name="Wednesday Oct 14")).to_be_visible()
    page.reload()
    expect(page.get_by_role("region")).to_have_count(1)
    expect(page.get_by_role("region", name="Wednesday Oct 14")).to_be_visible()


def test_disclosures_and_cancel_restore_each_view_and_initiating_focus(
    page: Page, live_server: LiveServer, run_request
):
    run = {
        **run_request,
        "sections": [
            {"distance_m": "1000", "target_pace_seconds_per_km": "390"},
            {"distance_m": "9007199254740993123", "target_pace_seconds_per_km": "390"},
        ],
    }
    assert page.request.post(f"{live_server.url}/v1/runs", data=run).status == 201
    page.goto(f"{live_server.url}/?view=day&date=2026-10-14")
    expect(page.get_by_role("link", name="Edit easy run")).to_contain_text(
        "9007199254740994.123 km · 2 sections · 6:30/km"
    )
    details = page.get_by_text("Hide details", exact=True)
    expect(details).to_be_visible()
    details.click()
    expect(page.get_by_text("Show details", exact=True)).to_be_visible()
    page.get_by_role("button", name="Week", exact=True).click()
    page.get_by_text("Show details", exact=True).click()
    expect(page.get_by_text("Hide details", exact=True)).to_be_visible()
    page.get_by_role("link", name="Edit easy run").click()
    page.get_by_role("link", name="Cancel", exact=True).click()
    expect(page.get_by_role("button", name="Week", exact=True)).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(page.get_by_text("Hide details", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="Edit easy run")).to_be_focused()
    page.get_by_role("button", name="Day", exact=True).click()
    expect(page.get_by_text("Show details", exact=True)).to_be_visible()
    page.get_by_role("link", name="Add run").click()
    page.get_by_role("link", name="Cancel", exact=True).click()
    expect(page.get_by_role("link", name="Add run")).to_be_focused()
    expect(page.get_by_text("Show details", exact=True)).to_be_visible()
    choose_date(page, "2026-10-15")
    choose_date(page, "2026-10-14")
    expect(page.get_by_text("Show details", exact=True)).to_be_visible()
    page.reload()
    expect(page.get_by_text("Hide details", exact=True)).to_be_visible()


def test_calendar_keyboard_months_contextual_week_and_escape(
    page: Page, live_server: LiveServer
):
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
    page.get_by_role("button", name="Next month").click()
    expect(page.get_by_role("heading", name="November 2026")).to_be_visible()
    page.get_by_role("button", name="Previous month").click()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).not_to_be_visible()
    expect(calendar).to_be_focused()
    calendar.click()
    page.get_by_role("button", name="Cancel", exact=True).click()
    expect(calendar).to_be_focused()


def test_confirmed_cross_week_save_selects_run_and_retry_only_reads(
    page: Page, live_server: LiveServer
):
    page.goto(f"{live_server.url}/?view=week&date=2026-10-14")
    page.get_by_role("link", name="Add run for Wednesday").click()
    page.get_by_label("Planned date").fill("2026-10-28")
    page.get_by_label("Run type").select_option("easy")
    page.get_by_label("Distance (km)").fill("1")
    page.get_by_label("Pace (m:ss/km)").fill("6:30")
    writes = []
    page.on(
        "request",
        lambda request: writes.append(request) if request.method == "POST" else None,
    )
    page.route(
        "**/v1/runs?*",
        lambda route: route.fulfill(status=503, json={"detail": "Read failed."}),
    )
    page.get_by_role("button", name="Save run", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Read failed.")
    expect(page.get_by_role("heading", level=3)).to_have_count(0)
    page.unroute("**/v1/runs?*")
    page.get_by_role("button", name="Retry", exact=True).click()
    expect(page.get_by_role("link", name="Edit easy run on 2026-10-28")).to_be_focused()
    expect(page.get_by_text("Show details", exact=True)).to_be_visible()
    expect(page).to_have_url(
        f"{live_server.url}/?week=2026-10-26&view=week&date=2026-10-28"
    )
    assert len(writes) == 1


def test_content_width_controls_week_layout_and_add_targets(
    page: Page, live_server: LiveServer, run_request
):
    assert (
        page.request.post(f"{live_server.url}/v1/runs", data=run_request).status == 201
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
        add = day.get_by_role("link", name="Add run").bounding_box()
        assert header and body and add and add["height"] >= 44
        if content_width == 559:
            assert body["y"] >= header["y"] + header["height"]
        else:
            assert body["x"] > header["x"] + header["width"]
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
