"""Manual creation observed through public browser and HTTP interactions."""

from uuid import UUID

import pytest
from playwright.sync_api import Page, Route, expect
from tests.fixtures.live_server import LiveServer


def open_form(page: Page, server: LiveServer) -> None:
    page.goto(f"{server.url}/?week=2026-10-12")
    page.get_by_role("region", name="Wednesday Oct 14").get_by_role(
        "link", name="Add run"
    ).click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Add a planned run")
    expect(page.get_by_label("Planned date", exact=True)).to_have_value("2026-10-14")
    expect(page.get_by_label("Run type", exact=True)).to_have_value("")


def fill_section(page: Page, number: int, distance: str, pace: str) -> None:
    section = page.get_by_role("group", name=f"Section {number}", exact=True)
    section.get_by_label("Distance (km)", exact=True).fill(distance)
    section.get_by_label("Pace (m:ss/km)", exact=True).fill(pace)


def test_manual_creation_read_display_restart_and_identical_retry(
    page: Page, live_server: LiveServer
):
    open_form(page, live_server)
    page.get_by_label("Start time").fill("07:30")
    page.get_by_label("Run type").select_option("interval")
    for number, pace in enumerate(("6:30", "5:45", "6:30"), 1):
        if number > 1:
            page.get_by_role("button", name="Add section", exact=True).click()
        fill_section(page, number, "1", pace)
    page.get_by_label("Personal note").fill("Keep the first section easy.")
    page.get_by_label("Trainer note").fill("Finish relaxed.")
    with page.expect_response("**/v1/runs") as response:
        page.get_by_role("button", name="Save run", exact=True).click()
    assert response.value.status == 201
    submitted = response.value.request.post_data_json
    assert submitted is not None
    assert str(UUID(submitted["id"])) == submitted["id"]
    assert submitted == {
        "id": submitted["id"],
        "planned_date": "2026-10-14",
        "planned_start_time": "07:30",
        "run_type": "interval",
        "sections": [
            {"distance_m": "1000", "target_pace_seconds_per_km": pace}
            for pace in ("390", "345", "390")
        ],
        "user_note": "Keep the first section easy.",
        "trainer_note": "Finish relaxed.",
    }
    read_url = f"{live_server.url}/v1/runs?start=2026-10-12&end=2026-10-19"
    saved = {**submitted, "revision": "1"}
    expect(page.get_by_role("heading", level=3)).to_have_text("Interval run @ 07:30")
    expect(page.get_by_text("Run saved.", exact=True)).to_have_count(0)
    expect(page).to_have_url(f"{live_server.url}/?week=2026-10-12")

    for restart in (False, True):
        if restart:
            live_server.restart()
            page.reload()
        assert page.request.get(read_url).json() == [saved]
        expect(page.get_by_role("region")).to_have_count(7)
        wednesday = page.get_by_role("region", name="Wednesday Oct 14")
        expect(wednesday.get_by_role("heading", level=3)).to_have_text(
            "Interval run @ 07:30"
        )
        expect(wednesday.get_by_role("listitem")).to_have_text(
            ["1 km6:30/km", "1 km5:45/km", "1 km6:30/km"]
        )
        expect(wednesday.get_by_text("Personal note", exact=True)).to_be_visible()
        expect(wednesday.get_by_text("Keep the first section easy.")).to_be_visible()
        expect(wednesday.get_by_text("Trainer note", exact=True)).to_be_visible()
        expect(wednesday.get_by_text("Finish relaxed.")).to_be_visible()
        expect(page.get_by_text("No runs planned", exact=True)).to_have_count(6)

    assert page.request.post(f"{live_server.url}/v1/runs", data=submitted).status == 200
    assert page.request.get(read_url).json() == [saved]
    page.reload()
    expect(page.get_by_role("heading", level=3)).to_have_count(1)


def test_section_editing_exact_conversion_and_save_to_changed_week(
    page: Page, live_server: LiveServer
):
    open_form(page, live_server)
    expect(page.get_by_role("button", name="Remove section 1")).to_be_disabled()
    expect(page.get_by_role("button", name="Move section 1 up")).to_be_disabled()
    expect(page.get_by_role("button", name="Move section 1 down")).to_be_disabled()
    fill_section(page, 1, "0001.01000", "0:01")
    page.get_by_role("button", name="Add section", exact=True).click()
    fill_section(page, 2, "9007199254740993.123", "150119987579016552:03")
    page.get_by_role("button", name="Add section", exact=True).click()
    fill_section(page, 3, "0001.01000", "0:01")
    page.get_by_role("button", name="Add section", exact=True).click()
    page.get_by_role("button", name="Remove section 4").click()
    page.get_by_role("button", name="Move section 2 up").click()
    expect(
        page.get_by_role("group", name="Section 1", exact=True).get_by_label(
            "Distance (km)"
        )
    ).to_have_value("9007199254740993.123")
    page.get_by_role("button", name="Move section 1 down").click()
    page.get_by_role("button", name="Move section 3 up").click()
    expect(page.get_by_role("button", name="Move section 3 down")).to_be_disabled()
    page.get_by_label("Planned date").fill("2026-10-21")
    page.get_by_label("Run type").select_option("hard")
    page.get_by_label("Personal note").fill("  \n  ")
    with page.expect_response("**/v1/runs") as response:
        page.get_by_role("button", name="Save run", exact=True).click()
    assert response.value.status == 201
    expect(page).to_have_url(f"{live_server.url}/?week=2026-10-19")
    saved = page.request.get(
        f"{live_server.url}/v1/runs?start=2026-10-19&end=2026-10-26"
    ).json()
    assert len(saved) == 1
    assert saved[0]["sections"] == [
        {"distance_m": "1010", "target_pace_seconds_per_km": "1"},
        {"distance_m": "1010", "target_pace_seconds_per_km": "1"},
        {
            "distance_m": "9007199254740993123",
            "target_pace_seconds_per_km": "9007199254740993123",
        },
    ]
    assert saved[0]["planned_start_time"] is None
    assert saved[0]["user_note"] is None
    assert saved[0]["trainer_note"] is None
    expect(page.get_by_role("heading", level=3)).to_have_text("Hard run")


def test_cancel_keeps_originating_week_without_creating_a_run(
    page: Page, live_server: LiveServer
):
    open_form(page, live_server)
    creates = []
    page.on(
        "request",
        lambda request: creates.append(request) if request.method == "POST" else None,
    )
    page.get_by_label("Planned date").fill("2026-10-28")
    fill_section(page, 1, "1", "6:30")
    page.get_by_role("link", name="Cancel", exact=True).click()
    expect(page).to_have_url(f"{live_server.url}/?week=2026-10-12")
    expect(page.get_by_text("No runs planned", exact=True)).to_have_count(7)
    assert creates == []


@pytest.mark.parametrize(
    ("distance", "pace", "invalid_field"),
    [
        ("0.0001", "6:30", "Distance (km)"),
        ("1e3", "6:30", "Distance (km)"),
        ("0", "6:30", "Distance (km)"),
        ("1", "5:75", "Pace (m:ss/km)"),
        ("1", "0:00", "Pace (m:ss/km)"),
    ],
)
def test_invalid_section_format_is_reported_without_rounding_or_losing_values(
    page: Page, live_server: LiveServer, distance: str, pace: str, invalid_field: str
):
    open_form(page, live_server)
    page.get_by_label("Run type").select_option("easy")
    fill_section(page, 1, distance, pace)
    page.get_by_role("button", name="Save run", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Check the marked fields")
    input = page.get_by_label(invalid_field, exact=True)
    expect(input).to_have_attribute("aria-invalid", "true")
    expect(input).to_be_focused()
    error_id = input.get_attribute("aria-describedby")
    expect(page.locator(f"#{error_id}")).to_be_visible()
    expect(page.get_by_label("Distance (km)", exact=True)).to_have_value(distance)
    expect(page.get_by_label("Pace (m:ss/km)", exact=True)).to_have_value(pace)
    assert (
        page.request.get(
            f"{live_server.url}/v1/runs?start=2026-10-12&end=2026-10-19"
        ).json()
        == []
    )


def test_api_field_errors_keep_correct_section_values_and_id_for_retry(
    page: Page, live_server: LiveServer
):
    open_form(page, live_server)
    page.get_by_label("Run type").select_option("interval")
    fill_section(page, 1, "1", "6:30")
    page.get_by_role("button", name="Add section", exact=True).click()
    fill_section(page, 2, "2", "5:45")
    page.get_by_label("Personal note").fill("Keep this note.\nAnd this line.")
    requests = []

    def reject(route: Route):
        requests.append(route.request.post_data_json)
        route.fulfill(
            status=422,
            json={
                "detail": [
                    {
                        "loc": ["body", "sections", 1, "target_pace_seconds_per_km"],
                        "type": "invalid_pace",
                        "msg": "This section's target pace is invalid.",
                    },
                    {
                        "loc": ["body", "run_type"],
                        "type": "invalid_type",
                        "msg": "Choose a supported run type.",
                    },
                ]
            },
        )

    page.route("**/v1/runs", reject)
    page.get_by_role("button", name="Save run", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text(
        "This section's target pace is invalid."
    )
    first = page.get_by_role("group", name="Section 1", exact=True)
    second = page.get_by_role("group", name="Section 2", exact=True)
    expect(first.get_by_label("Pace (m:ss/km)")).not_to_have_attribute(
        "aria-invalid", "true"
    )
    expect(second.get_by_label("Pace (m:ss/km)")).to_have_attribute(
        "aria-invalid", "true"
    )
    expect(second.get_by_text("This section's target pace is invalid.")).to_be_visible()
    expect(page.get_by_label("Run type")).to_have_attribute("aria-invalid", "true")
    expect(second.get_by_label("Distance (km)")).to_have_value("2")
    expect(second.get_by_label("Pace (m:ss/km)")).to_have_value("5:45")
    expect(page.get_by_label("Personal note")).to_have_value(
        "Keep this note.\nAnd this line."
    )
    page.unroute("**/v1/runs", reject)
    with page.expect_request("**/v1/runs") as retried:
        page.get_by_role("button", name="Save run", exact=True).click()
    assert retried.value.post_data_json == requests[0]
    expect(page.get_by_role("heading", level=3)).to_have_text("Interval run")


def test_nonexistent_montreal_time_returns_real_field_error_and_can_be_corrected(
    page: Page, live_server: LiveServer
):
    open_form(page, live_server)
    page.get_by_label("Planned date").fill("2026-03-08")
    page.get_by_label("Start time").fill("02:30")
    page.get_by_label("Run type").select_option("easy")
    fill_section(page, 1, "1", "6:30")
    with page.expect_response("**/v1/runs") as response:
        page.get_by_role("button", name="Save run", exact=True).click()
    assert response.value.status == 422
    expect(page.get_by_label("Start time")).to_have_attribute("aria-invalid", "true")
    expect(page.get_by_label("Start time")).to_have_value("02:30")
    expect(page.get_by_label("Planned date")).to_have_value("2026-03-08")
    page.get_by_label("Start time").fill("03:30")
    page.get_by_role("button", name="Save run", exact=True).click()
    expect(page).to_have_url(f"{live_server.url}/?week=2026-03-02")
    expect(page.get_by_role("heading", level=3)).to_have_text("Easy run @ 03:30")


@pytest.mark.parametrize("failure", ["network", "unavailable", "unreadable"])
def test_committed_uncertain_save_retries_same_payload_without_duplication(
    page: Page, live_server: LiveServer, failure: str
):
    open_form(page, live_server)
    page.get_by_label("Run type").select_option("easy")
    fill_section(page, 1, "1", "6:30")
    submitted = []

    def lose_response(route: Route):
        submitted.append(route.request.post_data_json)
        committed = route.fetch()
        assert committed.status == 201
        if failure == "network":
            route.abort("failed")
        elif failure == "unavailable":
            route.fulfill(
                status=503,
                json={
                    "detail": "Storage is temporarily unavailable; "
                    "retry with the same ID."
                },
            )
        else:
            route.fulfill(
                status=201, content_type="application/json", body="unreadable"
            )

    page.route("**/v1/runs", lose_response)
    page.get_by_role("button", name="Save run", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Saving could not be confirmed")
    expect(page.get_by_role("alert")).to_contain_text("unchanged values is safe")
    expect(page.get_by_label("Distance (km)")).to_have_value("1")
    expect(page.get_by_label("Pace (m:ss/km)")).to_have_value("6:30")
    expect(page.get_by_role("link", name="View submitted week")).to_have_attribute(
        "href", "/?week=2026-10-12"
    )
    page.unroute("**/v1/runs", lose_response)
    with page.expect_response("**/v1/runs") as retried:
        page.get_by_role("button", name="Save run", exact=True).click()
    assert retried.value.status == 200
    assert retried.value.request.post_data_json == submitted[0]
    expect(page.get_by_role("heading", level=3)).to_have_count(1)
    runs = page.request.get(
        f"{live_server.url}/v1/runs?start=2026-10-12&end=2026-10-19"
    ).json()
    assert len(runs) == 1
    assert runs[0]["id"] == submitted[0]["id"]


def test_editing_uncertain_save_conflicts_and_links_to_original_submitted_week(
    page: Page, live_server: LiveServer
):
    open_form(page, live_server)
    page.get_by_label("Run type").select_option("easy")
    fill_section(page, 1, "1", "6:30")
    submitted = []

    def lose_response(route: Route):
        submitted.append(route.request.post_data_json)
        assert route.fetch().status == 201
        route.abort("failed")

    page.route("**/v1/runs", lose_response)
    page.get_by_role("button", name="Save run", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Saving could not be confirmed")
    page.unroute("**/v1/runs", lose_response)
    page.get_by_label("Planned date").fill("2026-10-28")
    page.get_by_label("Personal note").fill("Edited after losing the response.")
    with page.expect_response("**/v1/runs") as conflicted:
        page.get_by_role("button", name="Save run", exact=True).click()
    assert conflicted.value.status == 409
    changed = conflicted.value.request.post_data_json
    assert changed is not None
    assert changed["id"] == submitted[0]["id"]
    expect(page.get_by_role("alert")).to_contain_text(
        "This run ID belongs to different saved data"
    )
    expect(page.get_by_role("alert")).to_contain_text(
        "Your earlier save may have succeeded"
    )
    expect(page.get_by_label("Planned date")).to_have_value("2026-10-28")
    expect(page.get_by_label("Personal note")).to_have_value(
        "Edited after losing the response."
    )
    assert (
        page.request.get(
            f"{live_server.url}/v1/runs?start=2026-10-26&end=2026-11-02"
        ).json()
        == []
    )
    stored = page.request.get(
        f"{live_server.url}/v1/runs?start=2026-10-12&end=2026-10-19"
    ).json()
    assert len(stored) == 1
    assert stored[0]["id"] == submitted[0]["id"]
    assert stored[0]["user_note"] is None
    page.get_by_role("link", name="View submitted week").click()
    expect(page).to_have_url(f"{live_server.url}/?week=2026-10-12")
    expect(page.get_by_role("heading", level=3)).to_have_text("Easy run")


@pytest.mark.parametrize("first_attempt_committed", [False, True])
def test_multiple_uncertain_dates_keep_a_link_to_the_week_that_actually_saved(
    page: Page, live_server: LiveServer, first_attempt_committed: bool
):
    open_form(page, live_server)
    page.get_by_label("Run type").select_option("easy")
    fill_section(page, 1, "1", "6:30")
    attempts = []

    def lose_responses(route: Route):
        attempts.append(route.request.post_data_json)
        if len(attempts) == 1:
            if first_attempt_committed:
                assert route.fetch().status == 201
        else:
            assert route.fetch().status == (409 if first_attempt_committed else 201)
        route.abort("failed")

    page.route("**/v1/runs", lose_responses)
    page.get_by_role("button", name="Save run", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Saving could not be confirmed")
    page.get_by_label("Planned date").fill("2026-10-28")
    with page.expect_request("**/v1/runs"):
        page.get_by_role("button", name="Save run", exact=True).click()
    expect(page.get_by_role("button", name="Save run", exact=True)).to_be_enabled()
    page.unroute("**/v1/runs", lose_responses)
    page.get_by_label("Personal note").fill("Another edit after an uncertain response.")
    with page.expect_response("**/v1/runs") as conflicted:
        page.get_by_role("button", name="Save run", exact=True).click()
    assert conflicted.value.status == 409
    expect(page.get_by_role("alert")).to_contain_text(
        "This run ID belongs to different saved data"
    )
    actual_week = "2026-10-12" if first_attempt_committed else "2026-10-26"
    link = page.get_by_role("alert").locator(f'a[href="/?week={actual_week}"]')
    expect(link).to_be_visible()
    link.click()
    expect(page).to_have_url(f"{live_server.url}/?week={actual_week}")
    expect(page.get_by_role("heading", level=3)).to_have_text("Easy run")
    assert attempts[0]["id"] == attempts[1]["id"]


@pytest.mark.parametrize(
    ("status", "explanation"),
    [
        (413, "Creation body exceeds 1 MiB (1,048,576 bytes)."),
        (415, "Creation requires a JSON content type."),
        (500, "An unexpected failure prevents the operation."),
    ],
)
def test_reported_save_failure_retains_values_and_actual_safe_explanation(
    page: Page, live_server: LiveServer, status: int, explanation: str
):
    open_form(page, live_server)
    page.get_by_label("Run type").select_option("long")
    fill_section(page, 1, "2", "5:45")
    page.get_by_label("Trainer note").fill("Keep this trainer note.")
    page.route(
        "**/v1/runs",
        lambda route: route.fulfill(status=status, json={"detail": explanation}),
    )
    page.get_by_role("button", name="Save run", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text(explanation)
    expect(page.get_by_label("Distance (km)")).to_have_value("2")
    expect(page.get_by_label("Pace (m:ss/km)")).to_have_value("5:45")
    expect(page.get_by_label("Trainer note")).to_have_value("Keep this trainer note.")
    expect(page.get_by_role("button", name="Save run", exact=True)).to_be_enabled()


def test_active_save_keeps_values_and_prevents_duplicate_submission(
    page: Page, live_server: LiveServer
):
    open_form(page, live_server)
    page.get_by_label("Run type").select_option("easy")
    fill_section(page, 1, "1", "6:30")
    held: list[Route] = []
    page.route("**/v1/runs", lambda route: held.append(route))
    with page.expect_request("**/v1/runs"):
        page.get_by_role("button", name="Save run", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Saving run...")
    expect(page.get_by_role("button", name="Save run", exact=True)).to_be_disabled()
    expect(page.get_by_role("button", name="Add section", exact=True)).to_be_disabled()
    expect(page.get_by_label("Distance (km)")).to_be_disabled()
    expect(page.get_by_label("Distance (km)")).to_have_value("1")
    page.keyboard.press("Enter")
    assert len(held) == 1
    held[0].fulfill(response=held[0].fetch())
    expect(page.get_by_role("heading", level=3)).to_have_text("Easy run")


def test_phone_layout_keyboard_access_action_order_and_error_placement(
    page: Page, live_server: LiveServer
):
    page.set_viewport_size({"width": 320, "height": 640})
    open_form(page, live_server)
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Aweille")).to_be_focused()
    page.keyboard.press("Tab")
    expect(page.get_by_label("Planned date")).to_be_focused()
    assert (
        page.get_by_label("Planned date").evaluate(
            "node => getComputedStyle(node).outlineWidth"
        )
        == "3px"
    )
    page.get_by_label("Run type").select_option("easy")
    page.get_by_role("button", name="Add section", exact=True).focus()
    page.keyboard.press("Enter")
    second = page.get_by_role("group", name="Section 2", exact=True)
    expect(second.get_by_label("Distance (km)")).to_be_focused()
    page.get_by_role("button", name="Remove section 1").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_label("Distance (km)")).to_be_focused()
    expect(page.get_by_role("button", name="Remove section 1")).to_be_disabled()
    fill_section(page, 1, "1", "5:75")
    page.get_by_role("button", name="Save run", exact=True).click()
    page.mouse.move(0, 0)
    distance = page.get_by_label("Distance (km)").bounding_box()
    pace = page.get_by_label("Pace (m:ss/km)").bounding_box()
    remove = page.get_by_role("button", name="Remove section 1").bounding_box()
    up = page.get_by_role("button", name="Move section 1 up").bounding_box()
    cancel = page.get_by_role("link", name="Cancel", exact=True).bounding_box()
    save = page.get_by_role("button", name="Save run", exact=True).bounding_box()
    error = page.get_by_role("alert").bounding_box()
    assert distance and pace and remove and up and cancel and save and error
    assert distance["y"] == pace["y"]
    assert distance["x"] < pace["x"]
    assert remove["x"] < up["x"]
    assert cancel["x"] < save["x"]
    assert error["y"] + error["height"] < save["y"]
    assert (
        page.get_by_role("button", name="Save run", exact=True).evaluate(
            "node => getComputedStyle(node).backgroundColor"
        )
        == "rgb(22, 101, 52)"
    )
    assert (
        page.get_by_role("button", name="Remove section 1").evaluate(
            "node => getComputedStyle(node).backgroundColor"
        )
        == "rgb(185, 28, 28)"
    )
    assert (
        page.get_by_role("link", name="Cancel", exact=True).evaluate(
            "node => getComputedStyle(node).backgroundColor"
        )
        == "rgb(255, 255, 255)"
    )
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_form_without_javascript_explains_disabled_creation(
    page: Page, live_server: LiveServer
):
    page.route("**/static/create_run.js", lambda route: route.abort())
    page.goto(f"{live_server.url}/runs/new?date=2026-10-14&week=2026-10-12")
    expect(page.get_by_role("status")).to_have_text(
        "JavaScript is required to save a run."
    )
    expect(page.get_by_role("button", name="Save run", exact=True)).to_be_disabled()
