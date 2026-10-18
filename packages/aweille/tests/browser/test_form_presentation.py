"""Form presentation and integration at the public page and HTTP seams."""

from playwright.sync_api import Page, expect
from tests.fixtures.live_server import LiveServer


def test_initial_editor_hides_fields_and_loaded_footer_stays_usable(
    page: Page, live_server: LiveServer, run_request
):
    assert (
        page.request.post(f"{live_server.url}/v1/runs", data=run_request).status == 201
    )
    page.set_viewport_size({"width": 320, "height": 640})
    held = []
    page.route("**/v1/runs/*", lambda route: held.append(route))
    page.goto(f"{live_server.url}/runs/{run_request['id']}/edit")
    expect(page.get_by_role("status")).to_contain_text("Loading run")
    expect(page.get_by_label("Planned date")).to_be_hidden()
    expect(page.get_by_role("button", name="Delete run", exact=True)).to_be_hidden()
    expect(page.locator("#run-form")).to_have_attribute("aria-busy", "true")
    held[0].fulfill(response=held[0].fetch())
    expect(page.get_by_label("Planned date")).to_be_visible()
    remove = page.get_by_role("button", name="Remove section 1", exact=True)
    assert remove.evaluate("node => getComputedStyle(node).borderTopWidth") == "0px"
    move = page.get_by_role("button", name="Move section 1 up", exact=True)
    expect(move.locator("svg")).to_be_visible()
    assert move.inner_text() == ""
    cancel = page.get_by_role("link", name="Cancel", exact=True).bounding_box()
    delete = page.get_by_role("button", name="Delete run", exact=True).bounding_box()
    save = page.get_by_role("button", name="Save changes", exact=True).bounding_box()
    assert cancel and delete and save
    assert cancel["y"] == delete["y"] == save["y"]
    assert cancel["x"] < delete["x"] < save["x"]
    assert save["y"] + save["height"] <= 640
    assert min(cancel["height"], delete["height"], save["height"]) >= 44
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_long_form_footer_clearance_thresholds_and_enlarged_text(
    page: Page, live_server: LiveServer
):
    page.goto(f"{live_server.url}/runs/new?date=2026-10-14")
    for _ in range(5):
        page.get_by_role("button", name="Add section", exact=True).click()
    page.get_by_label("Personal note").fill("Élève à Montréal.\n" * 40)
    page.get_by_label("Trainer note").fill("Review targets.\n" * 20)
    for width in (320, 390, 591, 592, 900, 1280):
        page.set_viewport_size({"width": width, "height": 700})
        expect(page.get_by_role("button", name="Toggle navigation")).to_have_attribute(
            "aria-expanded", "true" if width >= 900 else "false"
        )
        page.get_by_label("Trainer note").focus()
        page.get_by_label("Trainer note").evaluate(
            "node => node.scrollIntoView({block: 'center'})"
        )
        footer = page.locator(".form-footer").bounding_box()
        note = page.get_by_label("Trainer note").bounding_box()
        assert footer and note and footer["y"] + footer["height"] <= 700
        assert note["y"] + note["height"] <= footer["y"]
        date = page.get_by_label("Planned date").bounding_box()
        time = page.get_by_label("Start time").bounding_box()
        assert date and time
        assert time["y"] == date["y"]
        assert time["x"] > date["x"]
        assert (
            page.get_by_label("Planned date")
            .evaluate("node => getComputedStyle(node).fontFamily")
            .startswith('"IBM Plex Sans"')
        )
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.set_viewport_size({"width": 320, "height": 700})
    expect(page.get_by_role("button", name="Toggle navigation")).to_have_attribute(
        "aria-expanded", "false"
    )
    page.locator(".form-footer button, .form-footer a").evaluate_all(
        "nodes => nodes.forEach(node => { node.style.fontSize='26px'; "
        "node.style.lineHeight='1.5'; })"
    )
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    for action in page.locator(".form-footer button, .form-footer a").all():
        box = action.bounding_box()
        assert box and box["width"] >= 44 and box["height"] >= 44
    page.set_viewport_size({"width": 390, "height": 360})
    assert (
        page.locator(".form-footer").evaluate("node => getComputedStyle(node).position")
        == "static"
    )
    page.get_by_label("Trainer note").focus()
    expect(page.get_by_label("Trainer note")).to_be_focused()


def test_unavailable_form_script_keeps_schedule_navigation_operable(
    page: Page, live_server: LiveServer
):
    page.route("**/static/create_run.js", lambda route: route.abort())
    page.goto(f"{live_server.url}/runs/new")
    expect(page.get_by_role("button", name="Save run", exact=True)).to_be_disabled()
    page.get_by_role("link", name="Schedule", exact=True).click()
    expect(page.get_by_role("button", name="Day", exact=True)).to_be_visible()
