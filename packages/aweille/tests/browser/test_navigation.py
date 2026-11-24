"""Shared navigation through public pages, keyboard actions and layout."""

import re

import pytest
from playwright.sync_api import Page, expect
from tests.fixtures.live_server import LiveServer


def test_sidebar_collapse_drawer_focus_and_resize(page: Page, live_server: LiveServer):
    page.set_viewport_size({"width": 900, "height": 800})
    page.goto(live_server.url)
    menu = page.get_by_role("button", name="Toggle navigation")
    expect(menu).to_have_attribute("aria-expanded", "true")
    expect(page.locator("#application")).not_to_have_class(re.compile("drawer-mode"))
    box = page.locator(".shell").bounding_box()
    assert box and box["width"] == 628
    expect(page.get_by_text("Training", exact=True)).to_be_visible()
    expect(page.get_by_text("Planned", exact=True)).to_have_count(2)
    page.emulate_media(forced_colors="active")
    selected = page.get_by_role("link", name="Schedule", exact=True)
    assert selected.evaluate("node => getComputedStyle(node).borderLeftWidth") == "3px"
    assert selected.evaluate(
        "node => getComputedStyle(node).borderLeftColor !== "
        "getComputedStyle(node).backgroundColor"
    )
    page.emulate_media(forced_colors="none")
    page.get_by_role("button", name="Collapse navigation").click()
    expect(menu).to_have_attribute("aria-expanded", "false")
    expect(menu).to_be_focused()
    box = page.locator(".shell").bounding_box()
    assert box and box["width"] == 852
    page.set_viewport_size({"width": 390, "height": 844})
    menu.click()
    drawer = page.get_by_role("dialog", name="Navigation")
    expect(drawer).to_be_visible()
    expect(page.get_by_role("button", name="Close navigation")).to_be_focused()
    page.keyboard.press("Shift+Tab")
    expect(page.get_by_role("link", name="Schedule", exact=True)).to_be_focused()
    page.keyboard.press("Escape")
    expect(drawer).not_to_be_visible()
    expect(menu).to_be_focused()
    page.set_viewport_size({"width": 900, "height": 800})
    expect(menu).to_have_attribute("aria-expanded", "false")
    menu.click()
    expect(menu).to_have_attribute("aria-expanded", "true")


def test_drawer_schedule_keeps_invalid_create_draft_when_discard_declined(
    page: Page, live_server: LiveServer
):
    page.set_viewport_size({"width": 320, "height": 640})
    page.goto(f"{live_server.url}/planned-courses/new?date=2026-10-14&week=2026-10-12")
    page.get_by_label("Distance km").fill("partial")
    page.get_by_role("button", name="Save course", exact=True).click()
    expect(page.get_by_label("Distance km")).to_have_attribute("aria-invalid", "true")
    menu = page.get_by_role("button", name="Toggle navigation")
    menu.click()
    page.keyboard.press("Escape")
    expect(menu).to_be_focused()
    expect(page.get_by_label("Distance km")).to_have_value("partial")
    menu.click()
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("link", name="Schedule", exact=True).click()
    expect(menu).to_be_focused()
    expect(page.get_by_label("Distance km")).to_have_value("partial")
    expect(page.get_by_label("Distance km")).to_have_attribute("aria-invalid", "true")
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("link", name="Cancel", exact=True).click()
    expect(page.get_by_role("heading", level=1)).not_to_have_text("Add course")


def test_pending_create_navigation_warns_without_cancelling_write(
    page: Page, live_server: LiveServer
):
    page.goto(f"{live_server.url}/planned-courses/new?date=2026-10-14&week=2026-10-12")
    page.get_by_label("Course type").select_option("easy")
    page.get_by_label("Distance km").fill("1")
    page.get_by_label("Pace m:ss/km").fill("6:30")
    held = []
    page.route("**/v1/planned-courses", lambda route: held.append(route))
    page.get_by_role("button", name="Save course", exact=True).click()
    expect(page.get_by_role("button", name="Save course", exact=True)).to_be_disabled()
    messages = []

    def decline(dialog):
        messages.append(dialog.message)
        dialog.dismiss()

    page.once("dialog", decline)
    page.get_by_role("link", name="Schedule", exact=True).click()
    assert messages and "does not cancel" in messages[0]
    expect(page.get_by_label("Distance km")).to_have_value("1")
    assert len(held) == 1
    held[0].fulfill(response=held[0].fetch())
    expect(page.get_by_role("heading", level=3)).to_have_text("Easy course")


@pytest.mark.parametrize("width", [320, 390, 899, 900, 1280])
@pytest.mark.parametrize("screen", ["schedule", "create", "edit"])
def test_shared_layout_fonts_and_fallback(
    page: Page, live_server: LiveServer, planned_course_request, width: int, screen: str
):
    planned_course = {
        **planned_course_request,
        "user_note": "Élève à Montréal, cœur, Œuvre, Noël, façade, où",
    }
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses", data=planned_course
        ).status
        == 201
    )
    paths = {
        "schedule": "/?view=day&date=2026-10-14",
        "create": "/planned-courses/new?date=2026-10-14",
        "edit": f"/planned-courses/{planned_course['id']}/edit",
    }
    page.set_viewport_size({"width": width, "height": 800})
    page.goto(live_server.url + paths[screen])
    if screen == "edit":
        expect(page.get_by_label("Personal note")).to_have_value(
            planned_course["user_note"]
        )
    elif screen == "create":
        page.get_by_label("Personal note").fill(planned_course["user_note"])
    else:
        expect(page.get_by_role("heading", level=3)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.evaluate(
        "document.fonts.ready.then(() => "
        "document.fonts.check('400 16px \"IBM Plex Sans\"'))"
    )
    assert page.evaluate("document.fonts.check('500 16px \"IBM Plex Sans\"')")
    assert page.evaluate(
        "document.fonts.load('400 14px \"IBM Plex Mono\"').then(() => "
        "document.fonts.check('400 14px \"IBM Plex Mono\"'))"
    )
    assert page.evaluate(
        "performance.getEntriesByType('resource')"
        ".filter(e => e.name.endsWith('.woff2'))"
        ".every(e => new URL(e.name).origin === location.origin)"
    )
    assert (
        page.locator("h1").evaluate("node => getComputedStyle(node).fontWeight")
        == "500"
    )
    page.route("**/*.woff2", lambda route: route.abort())
    page.on("dialog", lambda dialog: dialog.accept())
    page.reload()
    expect(page.get_by_role("button", name="Toggle navigation")).to_be_enabled()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_constrained_application_uses_its_width_and_restores_desktop_choice(
    page: Page, live_server: LiveServer
):
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(live_server.url)
    menu = page.get_by_role("button", name="Toggle navigation")
    expect(menu).to_have_attribute("aria-expanded", "true")
    page.locator("#application").evaluate("node => node.style.width = '899px'")
    expect(menu).to_have_attribute("aria-expanded", "false")
    menu.click()
    expect(page.get_by_role("dialog", name="Navigation")).to_be_visible()
    page.locator("#application").evaluate("node => node.style.width = '900px'")
    expect(menu).to_have_attribute("aria-expanded", "true")
    expect(page.locator("#application")).not_to_have_class(re.compile("drawer-mode"))
    box = page.locator(".shell").bounding_box()
    assert box and box["width"] == 628
