# Aweille

I'm building Aweille to structure my running training. I want an editable weekly schedule, a record of planned workouts and actual results, and an external trainer agent that can manage my plan through an API.

This README defines the first version I want to build. The planned-run core, SQLite storage, create/read HTTP API, weekly browser view, and manual creation form are implemented.

The [wayfinder map](https://github.com/ArnaudJalbert/aweille/issues/1) records the first create, save, and display workflow and its implementation handoff. The code and tests define implemented behavior; the linked decisions describe that behavior and the remaining HTTP and browser work. SQLite storage is tracked in [PR #13](https://github.com/ArnaudJalbert/aweille/pull/13).

## Purpose

I want a simple framework to improve my running gradually. I like Runna's simplicity, but I find it expensive and hard to personalize. I want more flexibility, a web interface, and an app I can run locally without a hosting subscription.

I want my trainer agent to use my research and recorded history to help me design and adjust my training. I'm not currently training for a race. I'll focus the first version on running; broader fitness and health features can come later.

## Weekly schedule

I need to view and edit a week of planned workouts in the web interface. Each workout has:

- A date, with an optional specific time.
- A run type, such as easy, hard, interval, or long run.
- An ordered list of sections, each with a distance and target pace.
- Notes from me and the trainer agent.

A simple run uses one section. A workout can also specify, for example, 1 km at 6:30/km, then 1 km at 5:45/km, then 1 km at 6:30/km. Ordered distance-and-pace sections are enough for the first version.

I can reschedule planned workouts or mark them skipped. Skipped records remain available to the agent. Completed runs retain their planned targets separately from actual results, so future schedule adjustments preserve that history.

## Recording results

I'll enter results manually through one compact questionnaire. They describe the whole run.

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

I'll run the first version locally for myself. Local app hosting costs nothing; model access remains part of my external agent setup. Later, I may host it on my existing VPS or Fly.io so I can access it from anywhere. Deployment is outside the first version.

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

Within `aweille/api`, `routes/` holds the HTTP handlers, weekly page handler, and creation transport guard; `schemas/` holds the Pydantic request and response models and shared field types. The application factory, local startup module, and error handlers remain at the API root. HTTP tests mirror this layout under `tests/api`. Weekly templates and CSS/JavaScript live in `adapters/web`; browser checks live in `tests/browser`.

Both `aweille/api` and `aweille/adapters` depend on core. The local startup module also imports the concrete SQLite adapter. Core has no dependency on FastAPI, the SQLite driver, or concrete adapters.

The local entry point, `aweille.api.main:app`, constructs SQLite storage and passes it explicitly to `create_app(storage=...)`. This single application factory requires a core-owned `RunStorage` port and binds it to the use cases. HTTP handlers use those initialized use cases directly. I'll keep ports focused on dependencies required by current use cases.

The browser always calls the API for application data and changes. The trainer uses the same API. Page templates provide the interface structure; browser interactions go through the API. All business rules live in core, with HTTP and storage details in adapters.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, coding and testing rules, checks, and the pull request workflow.

## Public core interface

Import the models, storage port, errors, and use cases from `aweille.core`.

- `create_run(storage, *, id, planned_date, run_type, sections, planned_start_time=None, user_note=None, trainer_note=None)` returns `(stored_run, inserted)`. `inserted` is true only after storage commits a new run. An identical normalized retry returns the existing run and false; changed data under the same ID raises `RunConflict`.
- `read_runs(storage, *, start, end)` returns all runs in `[start, end)`, ordered by local date, local start time (untimed runs last), and canonical UUID string. `end` must be later than `start`.

Inputs use `UUID`, `date`, and optional naive `time` values with minute precision. Run type is a `RunType` enum member: `EASY`, `HARD`, `INTERVAL`, or `LONG`. The enum's string values remain `easy`, `hard`, `interval`, and `long`; adapters can parse them with `RunType(value)`.

Supply an ordered sequence of immutable `Section` values:

```python
from aweille.core import Distance, Pace, RunType, Section

run_type = RunType.INTERVAL
sections = [
    Section(distance=Distance(metres=1000), target_pace=Pace(seconds_per_km=390)),
    Section(distance=Distance(metres=1000), target_pace=Pace(seconds_per_km=345)),
    Section(distance=Distance(metres=1000), target_pace=Pace(seconds_per_km=390)),
]
```

`Distance` and `Pace` validate during construction. They accept positive integers only, rejecting booleans, floats, Decimal values, and strings without coercion. Distances use whole metres; paces use whole seconds per kilometre. Neither has a domain upper limit. `Section` requires these validated value objects. Both input and saved runs use this same section model. Read numeric values through `section.distance.metres` and `section.target_pace.seconds_per_km`.

`PlannedRun` is a frozen dataclass with a generated constructor. Its `__post_init__` only validates fields, without changing them. Direct construction requires a non-empty section tuple, trimmed nonblank notes or `None`, and a local time without a selected daylight-saving occurrence. `create_run` normalizes these inputs before calling the constructor: it copies section sequences into a tuple, trims notes, converts blank notes to `None`, and clears the local time's occurrence selection. Section order, repeated entries, and internal note spacing and line breaks are preserved. Run IDs remain caller-supplied `UUID` values; `str(run.id)` gives the canonical lowercase, hyphenated representation. Optional start times remain Montreal local clock times without an offset.

Invalid domain inputs raise `ValidationError`. Its `problems` tuple reports the first invalid field using a `ValidationProblem` with `loc`, `code`, and `message`, without raw input values. Constructor paths are relative to their value, such as `("metres",)`; invalid section-list entries use paths such as `("sections", 1)`. The HTTP adapter uses strict Pydantic request models, reports field and section locations, and adds `body` or `query` prefixes. Unknown enum strings are rejected without exposing the input.

Implement the core-owned `RunStorage` protocol to supply `save(run)` and `get(start, end)`. `save` atomically inserts a missing ID or returns its existing run unchanged, with `(stored_run, inserted)` as the result. A true insertion outcome means the write has committed. `get` returns every run in `[start, end)` from one committed snapshot, in any order; core applies sorting. Adapters return normalized `PlannedRun` values and translate driver errors to `StorageUnavailable` or `StorageFailure` with safe messages. Core preserves these failure categories. The application factory binds the supplied storage port to the functions with `functools.partial`.

The [data decision](https://github.com/ArnaudJalbert/aweille/issues/2#issuecomment-6100383988), [API contract](https://github.com/ArnaudJalbert/aweille/issues/3#issuecomment-6100699377), and [core implementation agreement](https://github.com/ArnaudJalbert/aweille/issues/5#issuecomment-6128315787) were synchronized with the implementation on October 13, 2026. The HTTP API uses `distance_m`, encoded as a positive whole-metre decimal-digit string such as `"1000"`, and `target_pace_seconds_per_km`, such as `"390"`. Numeric JSON values, signs, decimal points, exponent notation, and whitespace are invalid; responses use canonical digits. The browser will convert distances to and from kilometres exactly and format seconds for presentation. Future durations also use seconds. Planned start times retain the agreed Montreal clock-time meaning and minute precision.

Tests use the public constructors and use cases, with an in-memory storage fake for normal behavior and mocks for storage failures. Focused core verification is recorded in [planned-run core verification](docs/verification/planned-run-core.md). SQLite checks use the real adapter. HTTP checks use the application factory and real file-backed SQLite, with storage-port fault injection for unexpected failures.

`run.to_dict()` produces a fresh portable dictionary with canonical UUID, date, and time strings, ordered sections with decimal-digit metre and pace strings, and separate optional notes. `PlannedRun.from_dict(data)` reconstructs a validated model from that complete canonical representation. It raises `ValueError` for invalid encoded structure or representation and `ValidationError` for invalid domain values. These methods have no JSON or SQLite dependency. Parsing raw HTTP creation requests and their optional fields remains the request adapter's job.

## SQLite storage

Create the database once before using the adapter. Its parent directory must exist:

```sh
uv run aweille-init-db aweille.sqlite
```

The `aweille` package installs the `aweille-init-db` command, implemented in `aweille.adapters.create_database`. After installing Aweille, use `aweille-init-db <path>` from any working directory. The command creates the initial schema and planned-date index. It refuses an existing path without changing it and removes its new file if setup fails. Migrations remain outside this workflow.

Then import `SQLiteRunStorage` from `aweille.adapters`:

```python
from aweille.adapters import SQLiteRunStorage

storage = SQLiteRunStorage("aweille.sqlite", timeout=1.0)
```

Construction stores connection settings and assumes the database has been prepared correctly. It does not open the file, create tables, or inspect the schema. Local startup resolves the database path and rejects missing files; it does not create or repair the schema.

The adapter implements `RunStorage.save/get`. Each operation closes its connections, and reads use a committed snapshot. Separate application processes can safely insert the same ID. Operations fail if the file disappears, rather than creating replacement storage.

The adapter uses the model's dictionary representation, with JSON only for the sections column, preserving exact integers without an imposed numeric limit. Reads use `PlannedRun.from_dict`. Malformed saved data fails the whole operation with `StorageFailure`, including when retrieving an existing ID during a save. SQLite contention and temporary unavailability raise `StorageUnavailable`; other storage failures raise `StorageFailure`. Messages omit SQL, paths, and stored values. An uncertain commit failure can be resolved by retrying the same ID.

The default lock wait is one second, configurable through `timeout`. SQLite handles this bounded wait; the adapter adds no retry loop. Tests use real temporary files, short deliberate lock waits, and targeted driver fault injection. See [SQLite storage verification](docs/verification/sqlite-run-storage.md) and [testing research](docs/research/sqlite-storage-testing.md).

## Local HTTP API

Version 1 exposes `POST /v1/runs` for creation and `GET /v1/runs?start=YYYY-MM-DD&end=YYYY-MM-DD` for range reads. FastAPI registers the `/runs` resource under the `/v1` prefix.

Prepare the default persistent database once, then start the API on loopback:

```sh
uv sync --locked --all-packages
mkdir -p ~/.local/share/aweille
uv run aweille-init-db ~/.local/share/aweille/aweille.sqlite3
uv run uvicorn aweille.api.main:app --host 127.0.0.1 --port 8000
```

For an installed package, use `aweille-init-db` and `uvicorn` without `uv run`. Setup refuses an existing file, so skip it when restarting with an already prepared database.

The local entry point defaults to `~/.local/share/aweille/aweille.sqlite3`. To use another prepared file, set `AWEILLE_DB_PATH` before starting Uvicorn. It expands `~` and resolves the path once; relative paths use the startup working directory. Empty values, `:memory:`, missing files, and directories fail startup with a configuration error. Schema and connection failures return safe HTTP errors during requests. Startup never creates or repairs storage. Remote deployment is outside this workflow.

When embedding or testing the application, call `create_app(storage=...)` with an initialized `RunStorage` implementation. The factory reads no database configuration and creates no storage adapter.

Create the representative interval run:

```sh
curl -i http://127.0.0.1:8000/v1/runs \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "id": "54d97d4d-fadb-4d50-926e-af1bb26c711a",
  "planned_date": "2026-10-14",
  "planned_start_time": "07:30",
  "run_type": "interval",
  "sections": [
    {"distance_m": "1000", "target_pace_seconds_per_km": "390"},
    {"distance_m": "1000", "target_pace_seconds_per_km": "345"},
    {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
  ],
  "user_note": "Keep the first section easy.",
  "trainer_note": "Finish relaxed."
}
JSON

curl 'http://127.0.0.1:8000/v1/runs?start=2026-10-12&end=2026-10-19'
```

Creation returns `201` and the normalized run after commit. Replaying the same normalized run with its original ID returns `200`; changed data under that ID returns `409` without overwriting it. Time and notes may be omitted or null. Reads return a plain JSON array covering `[start, end)`, ordered by date, then start time with untimed runs last, then UUID. Both query dates are required; unknown fields and query parameters are rejected. Repeated scalar query parameters use their last value, following FastAPI's behavior.

Both endpoints return validated `RunResponse` models, with `SectionResponse` models preserving canonical distance and pace strings. The response includes all fields, including null time and notes. FastAPI documents creation, identical retries, and the read array in `/openapi.json`.

Validation and malformed JSON return `422` with `detail` problems containing `loc`, `type`, and `msg`. Other errors have a short `detail` string: `413` for a creation body over 1 MiB of received bytes, `415` for a non-JSON content type, `503` for temporary storage unavailability, and `500` for other operation failures. Exactly 1 MiB is permitted, including streamed requests without Content-Length. Responses omit raw input values and internal diagnostics; diagnostics go to local logs.

Stop Uvicorn and start it again with the same database path, then repeat the read. The saved run and its ID remain unchanged. Run the focused HTTP checks with:

```sh
uv run pytest packages/aweille/tests/api
```

## Weekly browser view

With the local server running, open [Aweille](http://127.0.0.1:8000/) in a browser. The view defaults to the current Monday-Sunday week in Montreal, using the browser's clock. To open the representative run's week, use [October 12 to 18, 2026](http://127.0.0.1:8000/?week=2026-10-12).

The selected Monday stays in `?week=YYYY-MM-DD`. Previous week, This week, and Next week controls sit below Sunday. Browser history and reload preserve selection. A valid non-Monday date selects its containing week; invalid or incomplete calendar ranges show an explanation and a This week recovery control.

Each day shows every run and section in API order. Distances are displayed exactly in kilometres, and paces in `m:ss/km`, including large values. Optional start times appear beside the run type; untimed runs have no time label. Personal note and Trainer note remain separate plain text with line breaks.

Reload or navigate to fetch newly API-created runs. An open tab keeps its selected week across Monday. Loading clears previous runs, failures offer Retry for the selected week, and late responses cannot replace a newer selection. JavaScript is required; a message explains when it cannot load the runs.

### Create a run in the browser

With the server running, open [October 12 to 18, 2026](http://127.0.0.1:8000/?week=2026-10-12) and choose Wednesday's Add run. The separate form prefills October 14 and lets you change it. Choose Interval, enter the optional start time `07:30`, and fill the first section with distance `1` km and pace `6:30`. Add two sections with `1` km at `5:45` and `1` km at `6:30`. Enter `Keep the first section easy.` as the Personal note and `Finish relaxed.` as the Trainer note, then choose Save run.

The form saves through `POST /v1/runs`, using the same API as external callers. It opens the saved run's week. Sections keep their order and repeated entries; Remove, Move up, and Move down change that order before saving. The last section cannot be removed. Distances convert exactly to whole-metre strings, and paces to whole-second strings. Values such as `0.0001` km or `5:75` are rejected without rounding. Empty time and notes become absent values. Cancel returns to the originating week without saving.

Save failures retain your fields and show errors beside affected inputs, with the overall explanation above Save run. A lost response, timeout, or server failure may leave the save uncertain. Retrying unchanged values uses the same UUID and payload, so it can confirm a committed run without creating a duplicate. If you change the values after an uncertain save and receive a conflict, use View submitted week to inspect the earlier run. When uncertain attempts span different weeks, the form keeps a link to each possible week. It never overwrites a saved run or generates a replacement ID on retry. Requests are limited to 1 MiB; reduce notes or sections if the API reports that limit.

Stop and restart the server using the same database file, then reopen the week. The saved run remains available through the browser and the range-read API above.

Install the browser used by the test suite, then run the focused checks:

```sh
uv run playwright install chromium
uv run pytest packages/aweille/tests/browser
```

These checks use the public browser and HTTP API. Separate API and manual creation scenarios use fresh real SQLite files, stop and restart Uvicorn with the same file, and retry the original creation without duplication. Read failures, lost save responses, conflicts, and reported field errors are injected at HTTP. Phone layout, keyboard focus, section editing, Montreal date boundaries, exact conversion and formatting, and plain-text notes are also checked.

## First-version completion

I'll consider the first version complete when I can use it for a full week:

1. I agree on a training program with a local agent.
2. The agent creates the week's workouts and sections through the API.
3. I see the week in the browser and can edit, move, or skip planned workouts.
4. I quickly record a completed run's results through the questionnaire.
5. The app keeps planned targets, actual results, and my notes and the agent's notes available for comparison.
6. When I ask, the agent reads that history and adjusts upcoming workouts without changing completed runs' targets.
7. The schedule and recorded history remain available after restarting the app.

## Deferred work

- Broader fitness and health tracking.
- Race-specific planning and complex training algorithms inside the app.
- Typed workout sections and advanced interval structures.
- Per-section actual results and automatic result imports.
- In-app training proposals and approval.
- Background training adjustments.
- Remote hosting.
