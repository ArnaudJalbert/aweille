"""Edit saved workouts through the weekly page and shared HTTP API."""

import re

import pytest
from playwright.sync_api import Page, expect
from tests.fixtures.live_server import LiveServer


def test_weekly_edit_prefill_partial_save_and_move(
    page: Page, live_server: LiveServer
) -> None:
    created = page.request.post(
        f"{live_server.url}/v1/planned-courses",
        data={
            "id": "00000000-0000-0000-0000-000000000032",
            "planned_date": "2026-10-14",
            "planned_start_time": "07:30",
            "course_type": "interval",
            "sections": [
                {"distance_m": "1000", "target_pace_seconds_per_km": "390"},
                {"distance_m": "1000", "target_pace_seconds_per_km": "390"},
            ],
            "user_note": "mine",
            "trainer_note": "trainer",
        },
    )
    assert created.status == 201
    page.goto(f"{live_server.url}/?week=2026-10-12&view=week")
    page.get_by_role("link", name="Edit interval course on 2026-10-14").click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Edit course")
    expect(page.get_by_label("Planned date")).to_have_value("2026-10-14")
    expect(page.get_by_label("Trainer note")).to_have_value("trainer")
    expect(page.get_by_role("group", name="Section 2")).to_be_visible()
    page.get_by_label("Planned date").fill("2026-10-21")
    with page.expect_response("**/v1/planned-courses/*") as result:
        page.get_by_role("button", name="Save changes").click()
    assert result.value.status == 200
    assert result.value.request.post_data_json == {"planned_date": "2026-10-21"}
    expect(page).to_have_url(re.compile(r"/\?week=2026-10-19(?:&.*)?$"))
    expect(page.get_by_role("heading", level=3)).to_have_text("Interval course")


def test_editor_prefills_exact_large_targets_and_order(
    page: Page, live_server: LiveServer
) -> None:
    planned_course_id = "00000000-0000-0000-0000-000000000032"
    huge = "9" * 5000
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses",
            data={
                "id": planned_course_id,
                "planned_date": "2026-10-14",
                "course_type": "interval",
                "sections": [
                    {"distance_m": huge, "target_pace_seconds_per_km": huge},
                    {"distance_m": "1000", "target_pace_seconds_per_km": "390"},
                    {"distance_m": huge, "target_pace_seconds_per_km": huge},
                ],
            },
        ).status
        == 201
    )
    page.goto(f"{live_server.url}/planned-courses/{planned_course_id}/edit")
    first = page.get_by_role("group", name="Section 1")
    last = page.get_by_role("group", name="Section 3")
    expected_km = huge[:-3] + "." + huge[-3:]
    expect(first.get_by_label("Distance km")).to_have_value(expected_km)
    expect(last.get_by_label("Distance km")).to_have_value(expected_km)
    with page.expect_response("**/v1/planned-courses/*") as result:
        page.get_by_role("button", name="Save changes").click()
    assert result.value.request.post_data_json == {}
    assert (
        page.request.get(
            f"{live_server.url}/v1/planned-courses/{planned_course_id}"
        ).json()["revision"]
        == "1"
    )


def test_stale_draft_requires_confirmed_reload(
    page: Page, live_server: LiveServer
) -> None:
    url = f"{live_server.url}/v1/planned-courses/00000000-0000-0000-0000-000000000032"
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses",
            data={
                "id": url.rsplit("/", 1)[1],
                "planned_date": "2026-10-14",
                "course_type": "easy",
                "sections": [
                    {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
                ],
            },
        ).status
        == 201
    )
    page.goto(
        f"{live_server.url}/planned-courses/{url.rsplit('/', 1)[1]}/edit"
        "?week=2026-10-12"
    )
    expect(page.get_by_label("Personal note")).to_have_value("")
    page.get_by_label("Personal note").fill("draft")
    assert (
        page.request.patch(
            url, data={"trainer_note": "trainer"}, headers={"If-Match": '"1"'}
        ).status
        == 200
    )
    page.get_by_role("button", name="Save changes").click()
    expect(page.get_by_text("Saved course changed")).to_be_visible()
    expect(page.get_by_role("alert")).to_contain_text("Saved course changed")
    expect(page.get_by_role("button", name="Save changes")).to_be_disabled()
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("button", name="Reload saved course").click()
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Reload saved course").click()
    expect(page.get_by_label("Personal note")).to_have_value("")
    expect(page.get_by_label("Trainer note")).to_have_value("trainer")
    expect(page.get_by_role("button", name="Save changes")).to_be_enabled()


def test_initial_missing_planned_course_never_enables_empty_form(
    page: Page, live_server: LiveServer
) -> None:
    page.goto(
        f"{live_server.url}/planned-courses/00000000-0000-0000-0000-000000000032/edit?week=2026-10-12"
    )
    expect(page.get_by_text("Course unavailable")).to_be_visible()
    expect(page.get_by_role("button", name="Save changes")).to_be_disabled()
    expect(
        page.get_by_role(
            "button", name="Delete course", exact=True, include_hidden=True
        )
    ).to_be_disabled()
    expect(page.get_by_label("Planned date")).to_be_disabled()
    expect(page.get_by_role("button", name="Reload saved course")).to_be_hidden()
    page.get_by_role("link", name="Cancel").click()
    expect(page).to_have_url(re.compile(r"/\?week=2026-10-12(?:&.*)?$"))
    expect(page.get_by_role("heading", level=1)).to_be_focused()


def test_uppercase_uuid_direct_link_loads_and_saves(
    page: Page, live_server: LiveServer
) -> None:
    planned_course_id = "54d97d4d-fadb-4d50-926e-af1bb26c711a"
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses",
            data={
                "id": planned_course_id,
                "planned_date": "2026-10-14",
                "course_type": "easy",
                "sections": [
                    {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
                ],
            },
        ).status
        == 201
    )
    page.goto(f"{live_server.url}/planned-courses/{planned_course_id.upper()}/edit")
    expect(page.get_by_role("button", name="Save changes")).to_be_enabled()
    page.get_by_label("Personal note").fill("edited")
    page.get_by_role("button", name="Save changes").click()
    expect(page).to_have_url(re.compile(r"/\?week=2026-10-12(?:&.*)?$"))
    assert (
        page.request.get(
            f"{live_server.url}/v1/planned-courses/{planned_course_id}"
        ).json()["user_note"]
        == "edited"
    )


def test_invalid_id_cannot_enable_editor(page: Page, live_server: LiveServer) -> None:
    page.goto(f"{live_server.url}/planned-courses/not-a-uuid/edit?week=2026-10-12")
    expect(page.get_by_text("Course unavailable")).to_be_visible()
    expect(page.get_by_role("button", name="Save changes")).to_be_disabled()


@pytest.mark.parametrize(
    "revision,planned_date,distance",
    [
        ("1", "2026-02-30", "1000"),
        ("1", "0000-01-01", "1000"),
        (1, "2026-10-14", "1000"),
        ("1", "2026-10-14", 1000),
    ],
)
def test_unreadable_success_cannot_enable_form(
    page: Page, live_server: LiveServer, revision, planned_date, distance
) -> None:
    planned_course_id = "00000000-0000-0000-0000-000000000032"
    page.route(
        "**/v1/planned-courses/*",
        lambda route: route.fulfill(
            status=200,
            json={
                "id": planned_course_id,
                "revision": revision,
                "planned_date": planned_date,
                "planned_start_time": None,
                "course_type": "easy",
                "sections": [
                    {"distance_m": distance, "target_pace_seconds_per_km": "390"}
                ],
                "user_note": None,
                "trainer_note": None,
            },
        ),
    )
    page.goto(f"{live_server.url}/planned-courses/{planned_course_id}/edit")
    expect(page.get_by_text("Could not load course")).to_be_visible()
    expect(page.get_by_role("button", name="Save changes")).to_be_disabled()
    expect(
        page.get_by_role(
            "button", name="Delete course", exact=True, include_hidden=True
        )
    ).to_be_disabled()


@pytest.mark.parametrize("changed_field", ["Planned date", "Start time"])
def test_montreal_gap_validation_retains_draft_for_correction(
    page: Page, live_server: LiveServer, changed_field: str
) -> None:
    planned_course_id = "00000000-0000-0000-0000-000000000032"
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses",
            data={
                "id": planned_course_id,
                "planned_date": (
                    "2026-03-07" if changed_field == "Planned date" else "2026-03-08"
                ),
                "planned_start_time": (
                    "02:30" if changed_field == "Planned date" else "03:30"
                ),
                "course_type": "easy",
                "sections": [
                    {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
                ],
            },
        ).status
        == 201
    )
    page.goto(
        f"{live_server.url}/planned-courses/{planned_course_id}/edit?week=2026-03-02"
    )
    expect(page.get_by_label("Start time")).to_have_value(
        "02:30" if changed_field == "Planned date" else "03:30"
    )
    page.get_by_label(changed_field).fill(
        "2026-03-08" if changed_field == "Planned date" else "02:30"
    )
    with page.expect_response("**/v1/planned-courses/*") as result:
        page.get_by_role("button", name="Save changes").click()
    assert result.value.status == 422
    expect(page.get_by_label("Start time")).to_have_attribute("aria-invalid", "true")
    expect(page.get_by_label("Planned date")).to_have_value("2026-03-08")
    expect(page.get_by_label("Start time")).to_have_value("02:30")
    expect(page.get_by_label("Start time")).to_be_focused()
    page.get_by_label("Start time").fill("")
    page.get_by_role("button", name="Save changes").click()
    expect(page).to_have_url(re.compile(r"/\?week=2026-03-02(?:&.*)?$"))
    saved = page.request.get(
        f"{live_server.url}/v1/planned-courses/{planned_course_id}"
    ).json()
    assert saved["planned_date"] == "2026-03-08"
    assert saved["planned_start_time"] is None


def test_api_field_errors_survive_dismissed_discard_prompts(
    page: Page, live_server: LiveServer
) -> None:
    planned_course_id = "00000000-0000-0000-0000-000000000032"
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses",
            data={
                "id": planned_course_id,
                "planned_date": "2026-10-14",
                "course_type": "easy",
                "sections": [
                    {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
                ],
            },
        ).status
        == 201
    )
    page.goto(
        f"{live_server.url}/planned-courses/{planned_course_id}/edit?week=2026-10-12"
    )
    expect(page.get_by_role("button", name="Save changes")).to_be_enabled()
    page.get_by_label("Personal note").fill("draft")
    page.route(
        "**/v1/planned-courses/*",
        lambda route: (
            route.fulfill(
                status=422,
                json={
                    "detail": [
                        {
                            "loc": ["body", "sections", 0, "distance_m"],
                            "type": "value_error",
                            "msg": "Distance rejected by API",
                        },
                        {
                            "loc": ["body", "user_note"],
                            "type": "value_error",
                            "msg": "Note rejected by API",
                        },
                    ]
                },
            )
            if route.request.method == "PATCH"
            else route.continue_()
        ),
    )
    page.get_by_role("button", name="Save changes").click()
    distance = page.get_by_role("group", name="Section 1").get_by_label("Distance km")
    note = page.get_by_label("Personal note")
    expect(distance).to_have_attribute("aria-invalid", "true")
    expect(note).to_have_attribute("aria-invalid", "true")
    for action in ("Cancel", "Reload"):
        dialogs = []

        def dismiss(dialog, recorded=dialogs):
            recorded.append((dialog.type, dialog.message))
            dialog.dismiss()

        page.once("dialog", dismiss)
        if action == "Cancel":
            page.get_by_role("link", name="Cancel").click()
            assert dialogs == [("confirm", "Discard your unsaved changes?")]
        else:
            page.evaluate("location.reload()")
            assert len(dialogs) == 1 and dialogs[0][0] == "beforeunload"
        expect(page).to_have_url(
            f"{live_server.url}/planned-courses/{planned_course_id}/edit?week=2026-10-12"
        )
        expect(note).to_have_value("draft")
        expect(distance).to_have_attribute("aria-invalid", "true")
        expect(note).to_have_attribute("aria-invalid", "true")
        error_id = distance.get_attribute("aria-describedby")
        assert error_id is not None
        expect(page.locator(f"#{error_id}")).to_have_text("Distance rejected by API")
        expect(page.locator("#user_note-error")).to_have_text("Note rejected by API")


@pytest.mark.parametrize("failure", ["network", "unavailable", "unreadable"])
def test_lost_success_requires_reload_and_keeps_draft_on_failed_read(
    page: Page, live_server: LiveServer, failure: str
) -> None:
    planned_course_id = "00000000-0000-0000-0000-000000000032"
    url = f"{live_server.url}/v1/planned-courses/{planned_course_id}"
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses",
            data={
                "id": planned_course_id,
                "planned_date": "2026-10-14",
                "course_type": "easy",
                "sections": [
                    {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
                ],
            },
        ).status
        == 201
    )
    page.goto(
        f"{live_server.url}/planned-courses/{planned_course_id}/edit?week=2026-10-12"
    )
    expect(page.get_by_role("button", name="Save changes")).to_be_enabled()
    page.get_by_label("Personal note").fill("draft")

    def commit_then_drop(route):
        result = route.fetch()
        assert result.status == 200
        if failure == "network":
            route.abort()
        elif failure == "unavailable":
            route.fulfill(status=503, json={"detail": "Result unavailable."})
        else:
            route.fulfill(
                status=200, body="unreadable", content_type="application/json"
            )

    page.route(
        "**/v1/planned-courses/*",
        lambda route: (
            commit_then_drop(route)
            if route.request.method == "PATCH"
            else route.continue_()
        ),
    )
    page.get_by_role("button", name="Save changes").click()
    expect(page.get_by_text("Saving could not be confirmed")).to_be_visible()
    expect(page.get_by_role("button", name="Save changes")).to_be_disabled()
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    page.unroute_all()
    assert page.request.get(url).json()["user_note"] == "draft"
    page.route(
        "**/v1/planned-courses/*",
        lambda route: (
            route.abort() if route.request.method == "GET" else route.continue_()
        ),
    )
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Reload saved course").click()
    expect(page.get_by_text("Could not load course")).to_be_visible()
    expect(page.get_by_label("Personal note")).to_have_value("draft")
    expect(page.get_by_role("button", name="Save changes")).to_be_disabled()
    page.unroute_all()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Reload saved course").click()
    expect(page.get_by_role("button", name="Save changes")).to_be_enabled()
    expect(page.get_by_label("Personal note")).to_have_value("draft")


@pytest.mark.parametrize("changed", [False, True])
def test_pending_save_warns_before_closing_dirty_editor(
    page: Page, live_server: LiveServer, changed: bool
) -> None:
    planned_course_id = "00000000-0000-0000-0000-000000000032"
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses",
            data={
                "id": planned_course_id,
                "planned_date": "2026-10-14",
                "course_type": "easy",
                "sections": [
                    {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
                ],
            },
        ).status
        == 201
    )
    page.goto(f"{live_server.url}/planned-courses/{planned_course_id}/edit")
    expect(page.get_by_role("button", name="Save changes")).to_be_enabled()
    pending = []
    page.route(
        "**/v1/planned-courses/*",
        lambda route: (
            pending.append(route)
            if route.request.method == "PATCH"
            else route.continue_()
        ),
    )
    if changed:
        page.get_by_label("Personal note").fill("draft")
    page.get_by_role("button", name="Save changes").click()
    expect(page.get_by_text("Saving changes...")).to_be_visible()
    messages = []

    def decline(dialog):
        messages.append(dialog.message)
        dialog.dismiss()

    page.once("dialog", decline)
    page.get_by_role("link", name="Schedule", exact=True).click()
    assert messages and "does not cancel" in messages[0]
    expect(page.get_by_role("status")).to_contain_text("Saving changes...")
    assert len(pending) == 1
    with page.expect_event("dialog") as warning:
        page.close(run_before_unload=True)
    assert warning.value.type == "beforeunload"
    warning.value.dismiss()


def test_edit_to_unreadable_final_week_stays_with_confirmed_saved_planned_course(
    page: Page, live_server: LiveServer
) -> None:
    planned_course_id = "00000000-0000-0000-0000-000000000032"
    url = f"{live_server.url}/v1/planned-courses/{planned_course_id}"
    assert (
        page.request.post(
            f"{live_server.url}/v1/planned-courses",
            data={
                "id": planned_course_id,
                "planned_date": "2026-10-14",
                "course_type": "easy",
                "sections": [
                    {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
                ],
            },
        ).status
        == 201
    )
    editor = (
        f"{live_server.url}/planned-courses/{planned_course_id}/edit?week=2026-10-12"
    )
    page.goto(editor)
    expect(page.get_by_label("Planned date")).to_have_value("2026-10-14")
    page.get_by_label("Planned date").fill("9999-12-31")
    with page.expect_response(url) as result:
        page.get_by_role("button", name="Save changes").click()
    assert result.value.status == 200
    expect(page).to_have_url(editor)
    expect(page.get_by_role("status")).to_contain_text("Changes saved")
    expect(page.get_by_label("Planned date")).to_have_value("9999-12-31")
    assert page.request.get(url).json()["revision"] == "2"
    page.reload()
    expect(page.get_by_label("Planned date")).to_have_value("9999-12-31")
    expect(page.get_by_role("button", name="Save changes")).to_be_enabled()


@pytest.mark.parametrize(
    "failure",
    ["missing-precondition", "bad-precondition", "oversized", "uncertain-noop"],
)
def test_write_recovery_states_keep_readable_draft_and_require_explicit_review(
    page: Page, live_server: LiveServer, planned_course_request, failure: str
):
    saved = page.request.post(
        f"{live_server.url}/v1/planned-courses", data=planned_course_request
    ).json()
    page.goto(f"{live_server.url}/planned-courses/{saved['id']}/edit")
    expect(page.get_by_role("button", name="Save changes")).to_be_enabled()
    note = page.get_by_label("Personal note")
    if failure != "uncertain-noop":
        note.fill("draft for review")

    def fail_write(route):
        if route.request.method != "PATCH":
            route.continue_()
        elif failure in ("missing-precondition", "bad-precondition"):
            headers = {
                key: value
                for key, value in route.request.headers.items()
                if key != "if-match"
            }
            if failure == "bad-precondition":
                headers["if-match"] = "invalid"
            route.fulfill(response=route.fetch(headers=headers))
        elif failure == "oversized":
            route.fulfill(status=413, json={"detail": "Request too large."})
        else:
            result = route.fetch()
            assert result.status == 200 and result.json()["revision"] == "1"
            route.fulfill(status=500, json={"detail": "Result unavailable."})

    page.route("**/v1/planned-courses/*", fail_write)
    page.get_by_role("button", name="Save changes").click()
    expect(page.get_by_role("alert")).to_be_visible()
    expect(note).to_have_value(
        "" if failure == "uncertain-noop" else "draft for review"
    )
    expect(note).to_be_enabled()
    if failure == "oversized":
        expect(page.get_by_role("alert")).to_contain_text(
            "Reduce the notes or sections"
        )
        expect(page.get_by_role("button", name="Save changes")).to_be_enabled()
    else:
        expect(page.get_by_role("button", name="Save changes")).to_be_disabled()
        expect(
            page.get_by_role("button", name="Delete course", exact=True)
        ).to_be_disabled()
        expect(page.get_by_role("button", name="Reload saved course")).to_be_visible()
    page.unroute_all()
    assert (
        page.request.get(f"{live_server.url}/v1/planned-courses/{saved['id']}").json()[
            "revision"
        ]
        == "1"
    )
