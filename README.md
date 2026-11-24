# Aweille

I'm building Aweille to structure my running training. I want an editable weekly schedule, a record of planned workouts and actual results, and an external trainer agent that can manage my plan through an API.

This README defines the first version I want to build. The planned-course core, SQLite storage, create/read/edit/delete HTTP API, Day/Week browser schedule, and manual creation and editing forms are implemented.

The code and tests define implemented behavior. The original [create-and-display map](https://github.com/ArnaudJalbert/aweille/issues/1) and [editing-and-deletion map](https://github.com/ArnaudJalbert/aweille/issues/17) preserve the planning decisions; their implementation workflows are complete. Older issue comments and verification reports describe dated stages, not current delivery status.

Skipping, actual results, and end-to-end use with a selected trainer agent remain unimplemented. [Secure remote access](https://github.com/ArnaudJalbert/aweille/issues/35) remains in planning. The [running-app redesign handoff](docs/design/implementation-handoff.md) specifies three production PRs and their acceptance; the redesign has not shipped. Future non-running training blocks are agreed product scope, not capabilities of the current planned-course API.

## Documentation

- [CONTEXT.md](CONTEXT.md) defines domain terms, including agreed future training blocks.
- [PRODUCT.md](PRODUCT.md) records product and design constraints; [DESIGN.md](DESIGN.md) records the accepted visual direction and exact implementation tokens. The browser applies the accepted redesign; [integration verification](docs/verification/redesign-acceptance.md) records checks and pending manual acceptance.
- [Training blocks](docs/design/training-blocks.md) separates future mixed-training rules from today's run-only model.
- [Planned-run editing and deletion](docs/design/planned-run-editing-and-deletion.md) records the implemented behavioral contract and public test seams.
- [CONTRIBUTING.md](CONTRIBUTING.md) defines the contributor workflow; [AGENTS.md](AGENTS.md) routes agent work to the relevant guidance.

## Purpose

I want a simple framework to improve my running gradually. I like Runna's simplicity, but I find it expensive and hard to personalize. I want more flexibility, a web interface, and an app I can run locally without a hosting subscription.

I want my trainer agent to use my research and recorded history to help me design and adjust my training. I'm not currently training for a race. I'll focus the first version on running; broader fitness and health features can come later.

## Weekly schedule

I need to view and edit a week of planned workouts in the web interface. Each workout has:

- A date, with an optional specific time.
- A course type, such as easy, hard, interval, or long.
- An ordered list of sections, each with a distance and target pace.
- Notes from me and the trainer agent.

A simple planned course uses one section. A workout can also specify, for example, 1 km at 6:30/km, then 1 km at 5:45/km, then 1 km at 6:30/km. Ordered distance-and-pace sections are enough for the first version.

Rescheduling and permanent deletion are implemented. Skipping remains planned and must retain the workout for the agent; deletion removes its content permanently. When results are implemented, completed runs must retain their planned targets separately from actual results so future schedule adjustments preserve that history.

## Recording results

Results entry is planned. I'll enter results manually through one compact questionnaire. They describe the whole run.

| Field | Requirement |
| --- | --- |
| Actual distance | Required. |
| Duration | Required. |
| Average pace | Calculated from distance and duration, and editable. |
| Perceived effort | Optional score from 1 to 10. |
| Average heart rate | Optional, in BPM. |
| Maximum heart rate | Optional maximum recorded during the run, in BPM. |
| My note | Optional. |

The agent can leave its own note on a workout, separate from mine. I need to keep planned targets and recorded results available so I can compare them and use that history to adjust my training.

## Trainer agent

My trainer will run as a separate local process and can reuse my existing hosted model access or subscriptions. I haven't selected the agent tool yet.

I'll discuss and agree on a program with the agent in our conversation. It will then write the schedule through Aweille's API so I don't have to copy it manually. Working agent access is part of the first version.

The API must support reading the schedule, workout sections, results, and notes; creating and editing planned workouts; rescheduling and skipping workouts; recording results; and leaving agent notes. The browser and agent both use this API for reads and changes.

When I ask for a review, the agent can read my recorded history and adjust upcoming workouts. Training reviews happen on request. I'll approve programs in the agent conversation for now.

## Technology

| Component | Choice |
| --- | --- |
| Language | Python. |
| Repository and package management | uv workspace with one `aweille` package for now. |
| HTTP API and web service | FastAPI. |
| Web interface | Jinja2 page templates, ordinary CSS, and small amounts of JavaScript that call the API. |
| Storage | SQLite through Python's standard `sqlite3` module. |
| Local server | Uvicorn. |
| Trainer | External local agent, to be selected. |

The app currently runs locally for me, with no app-hosting subscription. Model access remains part of my external agent setup. On October 17, 2026, I selected public HTTPS on my existing OVH VPS at `https://aweille.arnaudjalbert.com`, with one owner's Bitwarden passkey, browser sessions, a separate revocable trainer token, and SSH administration. These are agreed requirements in the [secure-access planning map](https://github.com/ArnaudJalbert/aweille/issues/35). Authentication and remote deployment are not implemented; the local startup and Docker workflows below bind to loopback.

The repository uses a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) with one member package named `aweille` in `packages/aweille`. It has its own `pyproject.toml`, and the workspace has one shared `uv.lock`. Additional packages can be split out later.

Within `aweille`:

- `aweille/core` contains entities, value objects, ports, and use cases.
- `aweille/api` contains HTTP routes, request and response models, error handling, and application wiring.
- `aweille/adapters` contains storage adapters, database setup, and browser templates and assets.

I prefer microservices. I'll start with one application service and split out additional services when there is a useful boundary.

## Architecture

I'll use a small hexagonal architecture within one package, with core business rules and adapters for HTTP and storage.

| Module | Responsibility |
| --- | --- |
| `aweille/core` | Entities, value objects, use cases, abstract port definitions, and all business rules. |
| `aweille/api` | HTTP routes, request and response models, error handling, the application factory, and local startup. |
| `aweille/adapters` | Concrete port implementations, SQLite storage, database setup, and browser templates and assets. |

Within `aweille/api`, `routes/` holds the HTTP handlers, weekly page handlers, and planned-course write transport guard; `schemas/` holds the Pydantic request and response models and shared field types. The application factory, local startup module, and error handlers remain at the API root. HTTP tests mirror this layout under `tests/api`. Weekly templates and CSS/JavaScript live in `adapters/web`; browser checks live in `tests/browser`.

Both `aweille/api` and `aweille/adapters` depend on core. The local startup module also imports the concrete SQLite adapter. Core has no dependency on FastAPI, the SQLite driver, or concrete adapters.

The local entry point, `aweille.api.main:app`, constructs SQLite storage and passes it explicitly to `create_app(storage=...)`. This single application factory requires a core-owned `PlannedCourseStorage` port and binds it to the use cases. HTTP handlers use those initialized use cases directly. I'll keep ports focused on dependencies required by current use cases.

The browser always calls the API for application data and changes. The trainer uses the same API. Page templates provide the interface structure; browser interactions go through the API. All business rules live in core, with HTTP and storage details in adapters.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, coding and testing rules, checks, and the pull request workflow.

The implemented [planned-run editing and deletion contract](docs/design/planned-run-editing-and-deletion.md) records the agreed behavior and test seams.

## Public core interface

Import the models, storage port, errors, and use cases from `aweille.core`.

- `create_planned_course(storage, *, id, planned_date, course_type, sections, planned_start_time=None, user_note=None, trainer_note=None)` returns `(stored_planned_course, inserted)`. `inserted` is true only after storage commits a new planned course. An identical normalized retry returns the existing planned course and false; changed data under the same ID raises `PlannedCourseConflict`.
- `read_planned_courses(storage, *, start, end)` returns all planned courses in `[start, end)`, ordered by local date, local start time (untimed planned courses last), and canonical UUID string. `end` must be later than `start`.
- `read_planned_course(storage, *, id)` returns one planned course or raises `PlannedCourseNotFound`.
- `update_planned_course(storage, *, id, expected_revision, planned_date=UNSET, planned_start_time=UNSET, course_type=UNSET, sections=UNSET, user_note=UNSET, trainer_note=UNSET)` changes only supplied fields. The current revision must match exactly or `PlannedCourseRevisionConflict` is raised. Changed normalized content increments the revision; no-ops do not.
- `delete_planned_course(storage, *, id, expected_revision)` permanently removes a matching planned course and reserves its UUID. A stale revision raises `PlannedCourseRevisionConflict`; an absent or already-deleted planned course raises `PlannedCourseNotFound`. Creation under a reserved UUID raises `PlannedCourseConflict`.

Inputs use `UUID`, `date`, and optional naive `time` values with minute precision. Course type is a `CourseType` enum member: `EASY`, `HARD`, `INTERVAL`, or `LONG`. The enum's string values remain `easy`, `hard`, `interval`, and `long`; adapters can parse them with `CourseType(value)`.

Supply an ordered sequence of immutable `Section` values:

```python
from aweille.core import Distance, Pace, CourseType, Section

course_type = CourseType.INTERVAL
sections = [
    Section(distance=Distance(metres=1000), target_pace=Pace(seconds_per_km=390)),
    Section(distance=Distance(metres=1000), target_pace=Pace(seconds_per_km=345)),
    Section(distance=Distance(metres=1000), target_pace=Pace(seconds_per_km=390)),
]
```

`Distance` and `Pace` validate during construction. They accept positive integers only, rejecting booleans, floats, Decimal values, and strings without coercion. Distances use whole metres; paces use whole seconds per kilometre. Neither has a domain upper limit. `Section` requires these validated value objects. Both input and saved planned courses use this same section model. Read numeric values through `section.distance.metres` and `section.target_pace.seconds_per_km`.

`PlannedCourse` is a frozen dataclass with a generated constructor. Its `__post_init__` only validates fields, without changing them. Direct construction requires a non-empty section tuple, trimmed nonblank notes or `None`, and a local time without a selected daylight-saving occurrence. `create_planned_course` normalizes these inputs before calling the constructor: it copies section sequences into a tuple, trims notes, converts blank notes to `None`, and clears the local time's occurrence selection. Section order, repeated entries, and internal note spacing and line breaks are preserved. Planned-course IDs remain caller-supplied `UUID` values; `str(planned_course.id)` gives the canonical lowercase, hyphenated representation. Optional start times remain Montreal local clock times without an offset.

Invalid domain inputs raise `ValidationError`. Its `problems` tuple reports the first invalid field using a `ValidationProblem` with `loc`, `code`, and `message`, without raw input values. Constructor paths are relative to their value, such as `("metres",)`; invalid section-list entries use paths such as `("sections", 1)`. The HTTP adapter uses strict Pydantic request models, reports field and section locations, and adds `body` or `query` prefixes. Unknown enum strings are rejected without exposing the input.

Implement the core-owned `PlannedCourseStorage` protocol with `save(planned_course)`, `get(start, end)`, `load(id)`, `replace(planned_course, *, expected_revision)`, and `delete(id, *, expected_revision)`. `save` atomically inserts a missing ID or returns its existing planned course unchanged, with `(stored_planned_course, inserted)` as the result. A true insertion outcome means the write has committed. `get` returns every planned course in `[start, end)` from one committed snapshot, in any order; core applies sorting. `load` returns the committed planned course for a UUID or `None` when absent. `replace` checks the saved revision atomically: it raises `PlannedCourseNotFound` if absent or `PlannedCourseRevisionConflict` if stale, returns the unchanged planned course on a normalized no-op, and otherwise commits the replacement with an incremented revision. `delete` checks existence and revision in the same transaction that removes workout content and permanently reserves only the UUID. It returns only after commit. Adapters return normalized `PlannedCourse` values and translate driver errors to `StorageUnavailable` or `StorageFailure` with safe messages. Core preserves these failure categories. The application factory binds the supplied storage port to the functions with `functools.partial`.

The [data decision](https://github.com/ArnaudJalbert/aweille/issues/2#issuecomment-6100383988), [API contract](https://github.com/ArnaudJalbert/aweille/issues/3#issuecomment-6100699377), and [core implementation agreement](https://github.com/ArnaudJalbert/aweille/issues/5#issuecomment-6128315787) were synchronized with the implementation on October 13, 2026. The HTTP API uses `distance_m`, encoded as a positive whole-metre decimal-digit string such as `"1000"`, and `target_pace_seconds_per_km`, such as `"390"`. Numeric JSON values, signs, decimal points, exponent notation, and whitespace are invalid; responses use canonical digits. The browser converts distances to and from kilometres exactly and formats seconds for presentation. Future durations also use seconds. Planned start times retain the agreed Montreal clock-time meaning and minute precision.

Tests use the public constructors and use cases, with an in-memory storage fake for normal behavior and mocks for storage failures. Focused core verification is recorded in [planned-run core verification](docs/verification/planned-run-core.md). SQLite checks use the real adapter. HTTP checks use the application factory and real file-backed SQLite, with storage-port fault injection for unexpected failures.

`planned_course.to_dict()` produces a fresh portable dictionary with canonical UUID, date, and time strings, ordered sections with decimal-digit metre and pace strings, separate optional notes, and a canonical positive revision string. `PlannedCourse.from_dict(data)` reconstructs a validated model from that complete canonical representation. It raises `ValueError` for invalid encoded structure or representation and `ValidationError` for invalid domain values. These methods have no JSON or SQLite dependency. Parsing raw HTTP creation requests and their optional fields remains the request adapter's job.

## SQLite storage

Create the database once before using the adapter. Its parent directory must exist:

```sh
uv run aweille-init-db aweille.sqlite
```

The `aweille` package installs the `aweille-init-db` command, implemented in `aweille.adapters.create_database`. After installing Aweille, use `aweille-init-db <path>` from any working directory. The command creates schema version 3 and the planned-date index. It refuses an existing path without changing it and removes its new file if setup fails. There is no migration: storage and startup reject version 1 and 2 files from before planned courses unchanged, so create a new database with `aweille-init-db`.

Then import `SQLitePlannedCourseStorage` from `aweille.adapters`:

```python
from aweille.adapters import SQLitePlannedCourseStorage

storage = SQLitePlannedCourseStorage("aweille.sqlite", timeout=1.0)
```

Construction stores connection settings and assumes the database has been prepared correctly. It does not open the file, create tables, or inspect the schema. Local startup resolves the database path and rejects missing files; it does not create or repair the schema.

The adapter implements `PlannedCourseStorage.save/get/load/replace/delete`. Each operation closes its connections; reads use committed data and range reads use one committed snapshot. `replace` acquires a write transaction before comparing revisions, so a competing edit cannot silently overwrite a newer planned course. Separate application processes can safely insert the same ID. Operations fail if the file disappears, rather than creating replacement storage.

The adapter uses the model's dictionary representation, with JSON only for the sections column, preserving exact integers without an imposed numeric limit. Reads use `PlannedCourse.from_dict`. Malformed saved data fails the whole operation with `StorageFailure`, including when retrieving an existing ID during a save. SQLite contention and temporary unavailability raise `StorageUnavailable`; other storage failures raise `StorageFailure`. Messages omit SQL, paths, and stored values. An uncertain `save` outcome can be checked by retrying the same ID and payload; after an uncertain `replace` or `delete`, reload and review before another write. Deletion and ID reservation commit together and survive restart. Deleted planned courses are excluded from all reads, and their UUIDs cannot be reused.

The default lock wait is one second, configurable through `timeout`. SQLite handles this bounded wait; the adapter adds no retry loop. Tests use real temporary files, short deliberate lock waits, and targeted driver fault injection. See [SQLite storage verification](docs/verification/sqlite-run-storage.md) and [testing research](docs/research/sqlite-storage-testing.md).

## Local HTTP API

Version 1 exposes `POST /v1/planned-courses` for creation, `GET /v1/planned-courses?start=YYYY-MM-DD&end=YYYY-MM-DD` for range reads, `GET /v1/planned-courses/{id}` for a single planned course, `PATCH /v1/planned-courses/{id}` for partial edits, and bodyless `DELETE /v1/planned-courses/{id}` for permanent deletion. FastAPI registers the `/planned-courses` resource under the `/v1` prefix.

Prepare the default persistent database once, then start the API on loopback:

```sh
uv sync --locked --all-packages
mkdir -p ~/.local/share/aweille
uv run aweille-init-db ~/.local/share/aweille/aweille.sqlite3
uv run uvicorn aweille.api.main:app --host 127.0.0.1 --port 8000
```

For an installed package, use `aweille-init-db` and `uvicorn` without `uv run`. Setup refuses an existing file, so skip it when restarting with an already prepared database.

The local entry point defaults to `~/.local/share/aweille/aweille.sqlite3`. To use another prepared file, set `AWEILLE_DB_PATH` before starting Uvicorn. It expands `~` and resolves the path once; relative paths use the startup working directory. Empty values, `:memory:`, missing files, and directories fail startup with a configuration error. Startup validates schema version 3 and saved data, rejecting incompatible databases before serving requests. Storage failures during requests return safe HTTP errors. Startup never creates or repairs storage. Remote deployment is outside this workflow.

When embedding or testing the application, call `create_app(storage=...)` with an initialized `PlannedCourseStorage` implementation. The factory reads no database configuration and creates no storage adapter.

### Run locally with Docker

Start Docker Desktop, then run:

```sh
./scripts/start-service.sh
```

The script builds from `uv.lock`, starts the service in the background, and waits for it to become healthy. Open [Aweille](http://localhost:8080/). Port 8080 is bound to localhost. Use `AWEILLE_PORT=8081 ./scripts/start-service.sh` to choose another port.

Docker mounts `~/.local/share/aweille` at `/data`, using the existing `aweille.sqlite3` file. Rebuilding or replacing the container preserves your planned courses. The launcher requires a prepared database and never initializes or replaces it. Set `AWEILLE_DATA_DIR` to use another directory containing `aweille.sqlite3`. The container runs with your user and group IDs so new SQLite files remain writable from the host.

From the repository root, use `docker compose logs -f` to follow logs, `docker compose stop` to stop the service, and the start script to rebuild and start it again. Docker's [unless-stopped restart policy](https://docs.docker.com/engine/containers/start-containers-automatically/) brings the service back when Docker starts, unless you stopped it explicitly. Docker Desktop must be running; the app can continue running after you close your terminal.

Create the representative interval planned course:

```sh
curl -i http://127.0.0.1:8000/v1/planned-courses \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "id": "54d97d4d-fadb-4d50-926e-af1bb26c711a",
  "planned_date": "2026-10-14",
  "planned_start_time": "07:30",
  "course_type": "interval",
  "sections": [
    {"distance_m": "1000", "target_pace_seconds_per_km": "390"},
    {"distance_m": "1000", "target_pace_seconds_per_km": "345"},
    {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
  ],
  "user_note": "Keep the first section easy.",
  "trainer_note": "Finish relaxed."
}
JSON

curl 'http://127.0.0.1:8000/v1/planned-courses?start=2026-10-12&end=2026-10-19'
```

Creation returns `201` and the normalized planned course after commit, with `Location: /v1/planned-courses/{id}`. Replaying the same normalized planned course with its original ID returns `200`; changed data under that ID returns `409` without overwriting it. Time and notes may be omitted or null. Reads return a plain JSON array covering `[start, end)`, ordered by date, then start time with untimed planned courses last, then UUID. Both query dates are required; unknown fields and query parameters are rejected. Repeated scalar query parameters use their last value, following FastAPI's behavior. Every complete planned course response includes a decimal-digit string `revision`; callers cannot supply it in POST or PATCH bodies.

Read and edit the example planned course using the revision returned by GET:

```sh
curl -i http://127.0.0.1:8000/v1/planned-courses/54d97d4d-fadb-4d50-926e-af1bb26c711a
curl -i -X PATCH http://127.0.0.1:8000/v1/planned-courses/54d97d4d-fadb-4d50-926e-af1bb26c711a \
  -H 'Content-Type: application/json' -H 'If-Match: "1"' \
  --data '{"user_note":"Keep it easy."}'
```

Single planned-course GET returns `200` with the complete planned course and an `ETag` containing its quoted revision, or `404` if absent. PATCH requires exactly one `If-Match` header containing that quoted positive revision. It changes only supplied fields; send null to clear an optional time or note. Non-nullable fields cannot be cleared, and sections replace the whole ordered list. A normalized no-op returns `200` with the unchanged revision and ETag; a change increments the revision and returns the complete planned course and new ETag. A missing header returns `428`, a malformed or repeated header `422`, a stale revision `412`, and an absent planned course `404`. After a stale or uncertain write, GET the planned course by ID and review its current fields and ETag before deciding whether to edit again. The server does not automatically retry an edit with a new revision.

DELETE requires the same single quoted `If-Match` revision as PATCH and returns an empty `204` without an ETag after commit. It rejects any received body with `422`; no Content-Type is required. Missing/malformed preconditions return `428`/`422`, stale live revisions return `412`, and missing or already-deleted planned courses return `404`. A repeated deletion is not a successful retry. POST under the deleted UUID returns `409`, even after restarting. After uncertain deletion, GET confirms current state or absence but not which caller removed the planned course. Recreating a workout needs a fresh UUID.

Successful planned course responses use validated `PlannedCourseResponse` models, with `SectionResponse` models preserving canonical distance and pace strings. Each complete response includes all fields, including null time and notes. `/openapi.json` documents creation, identical retries, range and single planned-course reads, partial edits, permanent deletion, and examples for stale writes, missing preconditions, and reload recovery. Planned-course API responses use `Cache-Control: no-store`.

Validation and malformed JSON return `422` with `detail` problems containing `loc`, `type`, and `msg`. Other errors have a short `detail` string: `413` for a POST or PATCH body over 1 MiB of received bytes, `415` for a non-JSON POST or PATCH content type, `503` for temporary storage unavailability, and `500` for other operation failures. Exactly 1 MiB is permitted, including streamed requests without Content-Length. Responses omit raw input values and internal diagnostics; diagnostics go to local logs.

Stop Uvicorn and start it again with the same database path, then repeat the read. The saved planned course and its ID remain unchanged. Run the focused HTTP checks with:

```sh
uv run pytest packages/aweille/tests/api
```

## Day/Week browser schedule

With the local server running, open [Aweille](http://127.0.0.1:8000/) in a browser. Day defaults to Montreal's current calendar date. Week shows all seven dates. To open the representative week, use [October 12 to 18, 2026](http://127.0.0.1:8000/?view=week&date=2026-10-14).

Week/Day preserves the selected date. Today selects Day using Montreal's date when pressed. The contextual calendar supports month navigation, arrow keys, Enter, Today or This Week, and Cancel/Escape. Relative headings retain exact dates underneath. Previous/next arrows beside the calendar move one day in Day or seven days in Week, preserving the selected weekday. Movement outside complete API week ranges is disabled.

The URL records `week`, `view` and `date`; reload/history restore selection with disclosure defaults. Existing `?week=YYYY-MM-DD` links remain valid. Without an explicit date, they select today within the current week or Monday in another week. Invalid or incomplete calendar ranges show an explanation with calendar and Today recovery.

Planned courses stay in API order, with a time column and Untimed label. Summary links show course type, exact total kilometres, section count and common or varied pace. Independent native Show/Hide controls reveal ordered sections and separate plain-text Personal note and Trainer note. Details default open in Day and closed in Week. Each view's manual choices survive same-week date/view changes and a form Cancel; week changes, ordinary reload and history restore defaults. There is no saved disclosure preference.

The desktop sidebar collapses completely; below 900px of application width it becomes a closed-by-default modal drawer. Menu toggles retain schedule state and form values. The drawer supports close/backdrop/Escape dismissal, keyboard focus containment and return. Aweille appears only in navigation.

Reload or navigate for fresh API data. Loading hides old planned courses, failures offer Retry for the current selection, and late reads cannot replace a newer selection. JavaScript-unavailable pages explain the unloaded state. A failed schedule read after a confirmed write retries only the read.

### Create a planned course in the browser

With the server running, open [October 12 to 18, 2026](http://127.0.0.1:8000/?view=week&date=2026-10-14) and choose Wednesday's Add course. The separate form prefills October 14 and lets you change it. Choose Interval, enter the optional start time `07:30`, and fill the first section with distance `1` km and pace `6:30`. Add two sections with `1` km at `5:45` and `1` km at `6:30`. Enter `Keep the first section easy.` as the Personal note and `Finish relaxed.` as the Trainer note, then choose Save course.

The form saves through `POST /v1/planned-courses`, using the same API as external callers. It selects the saved planned course's date in the originating view and focuses its summary. Sections keep their order and repeated entries; Remove, Move up, and Move down change that order before saving. The last section cannot be removed. Distances convert exactly to whole-metre strings, and paces to whole-second strings. Values such as `0.0001` km or `5:75` are rejected without rounding. Empty time and notes become absent values. Cancel restores originating selection, disclosures and focus without saving. Changed or invalid drafts ask before discard; pending writes explain that leaving does not cancel the request.

Save failures retain your fields and show errors beside affected inputs, with the overall explanation above the fields. A lost response, timeout, or server failure may leave the save uncertain. Retrying unchanged values uses the same UUID and payload, so it can confirm a committed planned course without creating a duplicate. If you change the values after an uncertain save and receive a conflict, use View submitted week to inspect the earlier planned course. When uncertain attempts span different weeks, the form keeps a link to each possible week. It never overwrites a saved planned course or generates a replacement ID on retry. Requests are limited to 1 MiB; reduce notes or sections if the API reports that limit.

Stop and restart the server using the same database file, then reopen the week. The saved planned course remains available through the browser and the range-read API above.

Install the browser used by the test suite, then run the focused checks:

```sh
uv run playwright install chromium
uv run pytest packages/aweille/tests/browser
```

These checks use the public browser and HTTP API. Separate API and manual creation scenarios use fresh real SQLite files, stop and restart Uvicorn with the same file, and retry the original creation without duplication. Read failures, lost save responses, conflicts, and reported field errors are injected at HTTP. Phone layout, keyboard focus, section editing, Montreal date boundaries, exact conversion and formatting, and plain-text notes are also checked.

### Edit or delete a planned course in the browser

Choose a planned course summary link. The editor loads saved fields and the current revision through the API. Save changes sends only changed fields, then selects and focuses the saved planned course, including after a cross-week move. Cancel restores originating selection and focus without a write and asks before discarding a dirty draft.

Delete course opens inline confirmation using the saved date and type, not draft values. Keep course preserves the draft without writing. Delete permanently discards unsaved edits and sends bodyless DELETE with the loaded revision, then returns to a freshly fetched originating week. Deletion cannot be undone.

Stale or uncertain edits/deletions keep the draft and block writes until Reload saved course succeeds with confirmation to discard changes. Failed reloads retain the draft; missing planned courses offer return without claiming which caller deleted them. Drafts exist only in page memory. Browser checks cover confirmation, cancellation, competing writes, lost responses, timeouts, recovery, phone layout, focus, restart persistence, and reserved-ID conflicts.

## First-version completion

I'll consider the first version complete when I can use it for a full week:

1. I agree on a training program with a local agent.
2. The agent creates the week's workouts and sections through the API.
3. I see the week in the browser and can edit, move, or skip planned workouts.
4. I quickly record a completed run's results through the questionnaire.
5. The app keeps planned targets, actual results, and my notes and the agent's notes available for comparison.
6. When I ask, the agent reads that history and adjusts upcoming workouts without changing completed runs' targets.
7. The schedule and recorded history remain available after restarting the app.

This full-week scenario is not complete. Planned-course creation, viewing, editing, rescheduling, deletion, and restart persistence are implemented; skipping, result recording, and trainer integration remain.

## Deferred work

- Stretching, strength/bodyweight training, and yoga as [independent training blocks](docs/design/training-blocks.md). Independence and ordering are agreed; detailed content, lifecycle, and implementation remain future work.
- Other fitness and health tracking beyond those training kinds.
- Race-specific planning and complex training algorithms inside the app.
- Typed workout sections and advanced interval structures.
- Per-section actual results and automatic result imports.
- In-app training proposals and approval.
- Background training adjustments.
- Authentication and remote hosting are selected but await the [secure-access design and implementation handoff](https://github.com/ArnaudJalbert/aweille/issues/35).
