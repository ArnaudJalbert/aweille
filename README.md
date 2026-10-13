# Aweille

I'm building Aweille to structure my running training. I want an editable weekly schedule, a record of planned workouts and actual results, and an external trainer agent that can manage my plan through an API.

This README defines the first version I want to build. The planned-run core and SQLite storage are implemented. HTTP and the web interface come next.

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
- `aweille/adapters` contains storage adapters, the API, web interface, and wiring.

I prefer microservices. I'll start with one application service and split out additional services when there is a useful boundary.

## Architecture

I'll use a small hexagonal architecture with two internal layers in the same package and focused files within each.

| Layer | Responsibility |
| --- | --- |
| `aweille/core` | Entities, value objects, use cases, abstract port definitions, and all business rules. |
| `aweille/adapters` | Concrete port implementations, storage access, the HTTP API, web interface, and wiring factory. |

Source-code dependencies point from adapters to core. Core has no dependency on FastAPI, the SQLite driver, or concrete adapters.

One factory in adapters constructs concrete dependencies and injects them into use cases through core-owned ports. The API uses those initialized use cases directly. I'll keep ports focused on dependencies required by current use cases.

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

Invalid domain inputs raise `ValidationError`. Its `problems` tuple reports the first invalid field using a `ValidationProblem` with `loc`, `code`, and `message`, without raw input values. Constructor paths are relative to their value, such as `("metres",)`; invalid section-list entries use paths such as `("sections", 1)`. The future request adapter maps constructor errors to request fields and section indexes, adds HTTP location prefixes, and selects status codes. Unknown enum strings raise `ValueError` during `RunType(value)` parsing; adapters translate that error without exposing the input.

Implement the core-owned `RunStorage` protocol to supply `save(run)` and `get(start, end)`. `save` atomically inserts a missing ID or returns its existing run unchanged, with `(stored_run, inserted)` as the result. A true insertion outcome means the write has committed. `get` returns every run in `[start, end)` from one committed snapshot, in any order; core applies sorting. Adapters return normalized `PlannedRun` values and translate driver errors to `StorageUnavailable` or `StorageFailure` with safe messages. Core preserves these failure categories. The application factory can bind storage to the functions with `functools.partial` when wiring is implemented.

The [data decision](https://github.com/ArnaudJalbert/aweille/issues/2#issuecomment-6100383988), [API contract](https://github.com/ArnaudJalbert/aweille/issues/3#issuecomment-6100699377), and [core implementation agreement](https://github.com/ArnaudJalbert/aweille/issues/5#issuecomment-6128315787) were synchronized with the implementation on October 13, 2026. The HTTP API remains planned. It uses `distance_m`, encoded as a positive whole-metre decimal-digit string such as `"1000"`, and `target_pace_seconds_per_km`, such as `"390"`. Numeric JSON values, signs, decimal points, exponent notation, and whitespace are invalid; responses use canonical digits. The browser converts distances to and from kilometres exactly and formats seconds for presentation. Future durations also use seconds. Planned start times retain the agreed Montreal clock-time meaning and minute precision.

Tests use the public constructors and use cases, with an in-memory storage fake for normal behavior and mocks for storage failures. Focused core verification is recorded in [planned-run core verification](docs/verification/planned-run-core.md). SQLite checks use the real adapter; HTTP checks belong to the next implementation step.

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

Construction stores connection settings and assumes the database has been prepared correctly. It does not open the file, create tables, or inspect the schema. Default-path selection, environment configuration, and application wiring belong to the API step; application startup does not create the schema automatically.

The adapter implements `RunStorage.save/get`. Each operation closes its connections, and reads use a committed snapshot. Separate application processes can safely insert the same ID. Operations fail if the file disappears, rather than creating replacement storage.

The adapter uses the model's dictionary representation, with JSON only for the sections column, preserving exact integers without an imposed numeric limit. Reads use `PlannedRun.from_dict`. Malformed saved data fails the whole operation with `StorageFailure`, including when retrieving an existing ID during a save. SQLite contention and temporary unavailability raise `StorageUnavailable`; other storage failures raise `StorageFailure`. Messages omit SQL, paths, and stored values. An uncertain commit failure can be resolved by retrying the same ID.

The default lock wait is one second, configurable through `timeout`. SQLite handles this bounded wait; the adapter adds no retry loop. Tests use real temporary files, short deliberate lock waits, and targeted driver fault injection. See [SQLite storage verification](docs/verification/sqlite-run-storage.md) and [testing research](docs/research/sqlite-storage-testing.md).

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
