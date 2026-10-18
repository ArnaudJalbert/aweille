import re

import pytest
from playwright.sync_api import Page, expect
from tests.fixtures.live_server import LiveServer


@pytest.fixture
def saved_run(page: Page, live_server: LiveServer):
    payload = {
        "id": "00000000-0000-0000-0000-000000000033",
        "planned_date": "2026-10-14",
        "run_type": "easy",
        "sections": [{"distance_m": "1000", "target_pace_seconds_per_km": "390"}],
        "user_note": "saved note",
    }
    assert page.request.post(f"{live_server.url}/v1/runs", data=payload).status == 201
    return payload


def test_inline_confirmation_keeps_draft_then_deletes_and_survives_restart(
    page: Page, live_server: LiveServer, saved_run
) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{live_server.url}/?week=2026-10-12&view=week")
    expect(page.get_by_role("button", name="Delete run", exact=True)).to_have_count(0)
    page.get_by_role("link", name="Edit easy run on 2026-10-14").click()
    expect(page.get_by_label("Personal note")).to_have_value("saved note")
    page.get_by_label("Personal note").fill("<script>draft</script>")
    page.get_by_label("Planned date").fill("2026-10-21")
    page.get_by_label("Run type").select_option("hard")
    writes = []
    page.on(
        "request",
        lambda request: (
            writes.append(request)
            if request.method in ("PATCH", "DELETE", "POST")
            else None
        ),
    )
    page.get_by_role("button", name="Delete run", exact=True).click()
    confirmation = page.get_by_role("region", name="Permanently delete this run?")
    expect(confirmation).to_contain_text("2026-10-14")
    expect(confirmation).to_contain_text("Easy")
    expect(confirmation).to_contain_text("cannot be undone")
    expect(confirmation).to_contain_text("unsaved edits will be discarded")
    expect(page.get_by_role("button", name="Keep run")).to_be_focused()
    expect(page.get_by_label("Planned date")).to_be_disabled()
    expect(page.get_by_role("button", name="Save changes")).to_be_disabled()
    page.keyboard.press("Enter")
    expect(confirmation).to_be_hidden()
    expect(page.get_by_role("button", name="Delete run", exact=True)).to_be_focused()
    expect(page.get_by_label("Personal note")).to_have_value("<script>draft</script>")
    assert writes == []
    assert (
        page.request.get(f"{live_server.url}/v1/runs/{saved_run['id']}").json()[
            "user_note"
        ]
        == "saved note"
    )
    page.get_by_role("button", name="Delete run", exact=True).click()
    with page.expect_response("**/v1/runs/*") as result:
        page.get_by_role("button", name="Delete permanently").click()
    assert result.value.status == 204
    assert result.value.request.method == "DELETE"
    assert result.value.request.headers["if-match"] == '"1"'
    assert result.value.request.post_data is None
    expect(page).to_have_url(re.compile(r"/\?week=2026-10-12(?:&.*)?$"))
    expect(page.get_by_role("heading", level=1)).to_be_focused()
    expect(page.locator(".run")).to_have_count(0)
    assert len(writes) == 1
    live_server.restart()
    page.reload()
    expect(page.locator(".run")).to_have_count(0)
    assert (
        page.request.get(f"{live_server.url}/v1/runs/{saved_run['id']}").status == 404
    )
    assert page.request.post(f"{live_server.url}/v1/runs", data=saved_run).status == 409


def test_stale_deletion_requires_confirmed_reload_and_new_confirmation(
    page: Page, live_server: LiveServer, saved_run
) -> None:
    url = f"{live_server.url}/v1/runs/{saved_run['id']}"
    page.goto(f"{live_server.url}/runs/{saved_run['id']}/edit?week=2026-10-12")
    expect(page.get_by_label("Personal note")).to_have_value("saved note")
    page.get_by_label("Personal note").fill("draft")
    assert (
        page.request.patch(
            url, data={"trainer_note": "trainer change"}, headers={"If-Match": '"1"'}
        ).status
        == 200
    )
    page.get_by_role("button", name="Delete run", exact=True).click()
    page.get_by_role("button", name="Delete permanently").click()
    expect(page.get_by_role("alert")).to_contain_text("Saved run changed")
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    expect(page.get_by_role("button", name="Save changes")).to_be_disabled()
    expect(page.get_by_role("button", name="Delete run", exact=True)).to_be_disabled()
    expect(page.get_by_role("button", name="Delete permanently")).to_be_hidden()
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("button", name="Reload saved run").click()
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    page.route("**/v1/runs/*", lambda route: route.abort())
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Reload saved run").click()
    expect(page.get_by_text("Could not load run")).to_be_visible()
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    expect(page.get_by_role("button", name="Delete run", exact=True)).to_be_disabled()
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("button", name="Retry", exact=True).click()
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    expect(page.get_by_text("Could not load run")).to_be_visible()
    page.unroute_all()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Reload saved run").click()
    expect(page.get_by_label("Personal note")).to_have_value("saved note")
    expect(page.get_by_label("Trainer note")).to_have_value("trainer change")
    expect(page.get_by_role("heading", level=1)).to_be_focused()
    expect(page.get_by_role("button", name="Delete permanently")).to_be_hidden()
    page.get_by_role("button", name="Delete run", exact=True).click()
    with page.expect_response(url) as result:
        page.get_by_role("button", name="Delete permanently").click()
    assert result.value.request.headers["if-match"] == '"2"'
    expect(page).to_have_url(re.compile(r"/\?week=2026-10-12(?:&.*)?$"))
    expect(page.get_by_role("heading", level=1)).to_be_focused()
    assert page.request.get(url).status == 404


def test_competing_deletion_keeps_draft_and_offers_return_without_claiming_success(
    page: Page, live_server: LiveServer, saved_run
) -> None:
    url = f"{live_server.url}/v1/runs/{saved_run['id']}"
    editor = f"{live_server.url}/runs/{saved_run['id']}/edit?week=2026-10-05"
    page.goto(editor)
    expect(page.get_by_label("Personal note")).to_have_value("saved note")
    page.get_by_label("Personal note").fill("draft")
    page.get_by_role("button", name="Delete run", exact=True).click()
    assert page.request.delete(url, headers={"If-Match": '"1"'}).status == 204
    page.get_by_role("button", name="Delete permanently").click()
    expect(page.get_by_role("alert")).to_contain_text("Run unavailable")
    expect(page.get_by_role("alert")).not_to_contain_text("deleted")
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    expect(page.get_by_role("button", name="Delete run", exact=True)).to_be_disabled()
    expect(page.get_by_role("button", name="Save changes")).to_be_disabled()
    expect(page.get_by_role("button", name="Reload saved run")).to_be_hidden()
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("link", name="Cancel").click()
    expect(page).to_have_url(editor)
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("link", name="Cancel").click()
    expect(page).to_have_url(re.compile(r"/\?week=2026-10-05(?:&.*)?$"))


@pytest.mark.parametrize(
    "outcome",
    [
        "lost-committed",
        "lost-uncommitted",
        "unreadable",
        "500",
        "503",
        "428",
        "header-422",
    ],
)
def test_uncertain_deletion_requires_get_recovery_not_write_retry(
    page: Page, live_server: LiveServer, saved_run, outcome
) -> None:
    url = f"{live_server.url}/v1/runs/{saved_run['id']}"
    page.goto(f"{live_server.url}/runs/{saved_run['id']}/edit?week=2026-10-12")
    expect(page.get_by_label("Personal note")).to_have_value("saved note")
    page.get_by_label("Personal note").fill("draft")
    deletes = []

    def fail_delete(route):
        if route.request.method != "DELETE":
            route.continue_()
            return
        deletes.append(route.request)
        if outcome == "lost-committed":
            assert route.fetch().status == 204
            route.abort()
        elif outcome == "lost-uncommitted":
            route.abort()
        elif outcome == "unreadable":
            route.fulfill(status=200, body="not a deletion confirmation")
        elif outcome == "header-422":
            route.fulfill(
                status=422,
                json={
                    "detail": [
                        {
                            "loc": ["header", "if-match"],
                            "type": "revision_precondition",
                            "msg": "Invalid revision",
                        }
                    ]
                },
            )
        else:
            route.fulfill(status=int(outcome), json={"detail": "Safe failure"})

    page.route("**/v1/runs/*", fail_delete)
    page.get_by_role("button", name="Delete run", exact=True).click()
    page.get_by_role("button", name="Delete permanently").click()
    title = (
        "Reload required"
        if outcome in ("428", "header-422")
        else "Deletion could not be confirmed"
    )
    expect(page.get_by_role("alert")).to_contain_text(title)
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    expect(page.get_by_role("button", name="Save changes")).to_be_disabled()
    expect(page.get_by_role("button", name="Delete run", exact=True)).to_be_disabled()
    expect(page.get_by_role("button", name="Delete permanently")).to_be_hidden()
    page.unroute_all()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Reload saved run").click()
    if outcome == "lost-committed":
        expect(page.get_by_role("alert")).to_contain_text("Run unavailable")
        expect(page.get_by_label("Personal note")).to_have_value("draft")
        expect(
            page.get_by_role("button", name="Delete run", exact=True)
        ).to_be_disabled()
        assert page.request.get(url).status == 404
    else:
        expect(page.get_by_label("Personal note")).to_have_value("saved note")
        expect(
            page.get_by_role("button", name="Delete run", exact=True)
        ).to_be_enabled()
        expect(page.get_by_role("button", name="Delete permanently")).to_be_hidden()
        assert page.request.get(url).status == 200
    assert len(deletes) == 1


def test_rejected_deletion_keeps_draft_and_allows_fresh_confirmation(
    page: Page, live_server: LiveServer, saved_run
) -> None:
    page.goto(f"{live_server.url}/runs/{saved_run['id']}/edit")
    expect(page.get_by_label("Personal note")).to_have_value("saved note")
    page.get_by_label("Personal note").fill("draft")
    page.route(
        "**/v1/runs/*",
        lambda route: (
            route.fulfill(
                status=422,
                json={
                    "detail": [
                        {
                            "loc": ["body"],
                            "type": "body_forbidden",
                            "msg": "Empty body required",
                        }
                    ]
                },
            )
            if route.request.method == "DELETE"
            else route.continue_()
        ),
    )
    page.get_by_role("button", name="Delete run", exact=True).click()
    page.get_by_role("button", name="Delete permanently").click()
    expect(page.get_by_role("alert")).to_contain_text("Could not delete this run")
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    expect(page.get_by_role("button", name="Save changes")).to_be_enabled()
    expect(page.get_by_role("button", name="Delete run", exact=True)).to_be_enabled()


def test_pending_deletion_blocks_competing_actions_then_timeout_requires_reload(
    page: Page, live_server: LiveServer, saved_run
) -> None:
    page.goto(f"{live_server.url}/runs/{saved_run['id']}/edit")
    expect(page.get_by_label("Personal note")).to_have_value("saved note")
    page.get_by_label("Personal note").fill("draft")
    pending = []
    page.route(
        "**/v1/runs/*",
        lambda route: (
            pending.append(route)
            if route.request.method == "DELETE"
            else route.continue_()
        ),
    )
    page.get_by_role("button", name="Delete run", exact=True).click()
    page.get_by_role("button", name="Delete permanently").click()
    expect(page.get_by_role("status")).to_contain_text("Deleting run...")
    for name in ("Delete permanently", "Keep run", "Save changes", "Delete run"):
        expect(page.get_by_role("button", name=name, exact=True)).to_be_disabled()
    expect(page.get_by_label("Personal note")).to_be_disabled()
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("link", name="Cancel").click()
    expect(page.get_by_role("status")).to_contain_text("Deleting run...")
    expect(page.get_by_text("Deletion could not be confirmed")).to_be_visible(
        timeout=20000
    )
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    expect(page.get_by_role("button", name="Delete run", exact=True)).to_be_disabled()
    assert len(pending) == 1
