# Aweille

I'm building Aweille to structure my running training. I want an editable weekly schedule, a record of planned workouts and actual results, and an external trainer agent that can manage my plan through an API.

This README defines the first version I want to build. The planned-run core is implemented. HTTP, SQLite persistence, and the web interface come next.

I'm planning the first create, save, and display workflow in the [wayfinder map](https://github.com/ArnaudJalbert/aweille/issues/1) before starting implementation.

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

Use uv and Python 3.13 or later. `.python-version` selects 3.13 for local development. Run these commands from the repository root:

```sh
uv sync --locked --all-packages
uv run pytest
uv run pytest packages/aweille/tests/use_cases/test_create_run.py
uv run pytest packages/aweille/tests/use_cases/test_read_runs.py
uv run ty check
uv run ruff check .
uv run ruff format --check .
```

Use `uv run ruff format .` to format changes. The workspace's development dependencies are pytest, ty, and Ruff. The `aweille` package has no runtime dependencies; Montreal scheduling uses Python's `zoneinfo` and the system IANA timezone database.

### Public core interface

Import the models, storage port, errors, and use cases from `aweille.core`.

Each use case, model, and error has its own named file under `core/use_cases`, `core/models`, or `core/errors`. Shared validators have their own modules. Tests mirror the use cases, with shared fixtures registered through `conftest.py`. Follow the [file organization rule](AGENTS.md#file-organization) when adding components.

- `create_run(storage, *, id, planned_date, run_type, sections, planned_start_time=None, user_note=None, trainer_note=None)` returns `(stored_run, inserted)`. `inserted` is true only after storage commits a new run. An identical normalized retry returns the existing run and false; changed data under the same ID raises `RunConflict`.
- `read_runs(storage, *, start, end)` returns all runs in `[start, end)`, ordered by local date, local start time (untimed runs last), and canonical UUID string. `end` must be later than `start`.

Inputs use `UUID`, `date`, and optional naive `time` values with minute precision. Run type is `easy`, `hard`, `interval`, or `long`. Supply an ordered sequence of `SectionInput(distance_km=Decimal(...), target_pace_seconds_per_km=int_value)` values. Distances must be finite, positive, and expressible in whole metres; paces must be positive integers. Binary floating-point inputs and booleans are rejected. JSON strings are parsed by the future API adapter.

`PlannedRun` and its `Section` values are immutable. Normalized sections use integer `distance_m` and integer `target_pace_seconds_per_km`, with no domain upper limit. Run IDs remain `UUID` values; `str(run.id)` gives the canonical lowercase, hyphenated representation. Optional times remain Montreal local clock times without an offset or selected daylight-saving occurrence. Blank notes become `None`; other notes retain internal spacing and line breaks after outer whitespace is trimmed.

Invalid domain inputs raise `ValidationError`. Its `problems` tuple reports the first invalid field using a `ValidationProblem` with `loc`, `code`, and `message`, without raw input values. A section path can be `("sections", 1, "distance_km")`. HTTP location prefixes and status codes belong to adapters.

Implement the core-owned `Storage` protocol to supply `insert_if_absent(run)` and `read_range(start, end)`. Adapters return normalized `PlannedRun` values, commit atomically, and translate driver errors to `StorageUnavailable` or `StorageFailure` with safe messages. Core preserves these failure categories. The application factory can bind storage to the functions with `functools.partial` when wiring is implemented.

Tests use the public use cases, with an in-memory storage fake for normal behavior and mocks for storage failures. Focused verification is recorded in [planned-run core verification](docs/verification/planned-run-core.md). Real HTTP and SQLite checks belong to the next implementation step.

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
