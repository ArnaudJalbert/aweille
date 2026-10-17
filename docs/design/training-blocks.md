# Multiple training blocks per day

Design agreement, October 17, 2026. Arnaud wants to add stretching, strength/bodyweight training, and yoga in the future. He confirmed that these are independent blocks rather than mandatory parts of a grouped session.

## Agreed concepts

A day groups zero or more training blocks. Each block represents one independently scheduled activity. Two blocks of the same kind can share a day, just as a run and yoga can. Moving or skipping one block does not imply changing the others.

A running block contains ordered run sections. The sections stay inside that run; they do not become separate calendar entries. Stretching before a run may be its own independent block when that is what the user plans.

Training kind distinguishes running, stretching, strength training, and yoga. Run type distinguishes easy, hard, interval, and long runs within the running kind. Yoga is not another run type. The glossary in [CONTEXT.md](../../CONTEXT.md) records these terms.

Arnaud selected chronological ordering for timed blocks, followed by untimed blocks. Manual within-day ordering is not part of this design. Keep a stable tie-breaker for equal or absent times; the current run interface uses UUID.

## What exists today

[read_runs](../../packages/aweille/src/aweille/core/use_cases/read_runs.py) returns every matching run, sorted by date and optional time, with untimed runs last and UUID as the final tie-breaker. The [weekly renderer](../../packages/aweille/src/aweille/adapters/web/static/weekly.js) groups all matching runs under each day. The production app already supports several runs on the same date.

The restriction is the kind of record. [PlannedRun](../../packages/aweille/src/aweille/core/models/planned_run.py) requires a run type and nonempty run sections, and each [Section](../../packages/aweille/src/aweille/core/models/section.py) requires distance and target pace. These are useful running rules, not appropriate requirements for a yoga or strength block.

The original visual prototype used one sample run per day despite the real app supporting more. The revised prototype uses a list of blocks for each day.

## Design consequence

Give the day one date heading, a list of independently identifiable blocks, and a day-level Add block action. Keep a clear separator between sibling blocks; do not wrap the entire day as if it were one workout.

Each block has its own kind/name, optional time, relevant summary, and detail. A run may show distance, pace, and ordered sections. A stretching or yoga example may show duration. A strength example may show an exercise count. These are proposed summary treatments; detailed non-running editors and metrics remain to be designed.

Arnaud approved the collapsible per-block details in the prototype. In the schedule, details start collapsed while the block's name, optional time, and concise summary remain visible. Expanding a block reveals its sections and notes without changing sibling blocks; several disclosures may remain open together. Preserve keyboard access and a visible disclosure indicator. This is an approved design pattern, with production implementation deferred.

Never label a day containing yoga as empty merely because it has no runs. Avoid a single completion control, edit action, pace, or total distance that appears to describe every block. Distances, durations, and exercise counts are different quantities; do not add them into one unexplained daily total.

The [prototype](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-ui-prototype.html) contains a mixed-training mode alongside the runs-only study. It lets the user add illustrative blocks locally and inspect their individual details. All examples are design fixtures, not a training recommendation or saved data.

The 360px and 728px preview checks cover several blocks in one day, repeated blocks of the same kind, timed-first ordering, preservation of a sibling run's sections and notes after addition, and a non-running day remaining nonempty. Both week layouts and the existing run-form specimen fit these widths without horizontal overflow.

## Implementation direction when another kind is built

Keep shared scheduling concerns together: identity, planned date, optional start time, and lifecycle. Keep the training content specific to its kind. Do not add yoga or strength as values in RunType, force non-running activities into distance-and-pace sections, or start with one record containing every possible nullable metric.

The existing run model, API, and stored records remain unchanged during this design study. A future implementation must specify the shared scheduling interface, kind-specific validation and editing, and compatibility with existing run IDs, revisions, clients, and saved data. The current design is not a database migration plan.

Do not introduce a Session entity, reusable-routine catalog, generic exercise hierarchy, or universal results form merely to display several blocks in one day.

## Still open

- Detailed content and editing for stretching, strength, and yoga.
- Completion, skipping, results, and recovery behavior for each kind. Independence is agreed; the full lifecycle contract is not.
- Whether optional grouping becomes useful later. Independent blocks do not require grouping now.
