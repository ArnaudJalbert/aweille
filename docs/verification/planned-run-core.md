# Planned-run core verification

Verified locally on October 13, 2026, with Python 3.13.14 for [issue #5](https://github.com/ArnaudJalbert/aweille/issues/5). The [original implementation agreement](https://github.com/ArnaudJalbert/aweille/issues/5#issuecomment-6128315787) and the README's [review contract update](../../README.md#public-core-interface) describe the agreed interfaces and revised units.

This is a historical verification snapshot of the creation/read core, not a report on the current full suite. Later editing, deletion, revisions, schema upgrades, HTTP, and browser work are described in the [README](../../README.md) and [editing/deletion contract](../design/planned-run-editing-and-deletion.md).

## Test seams

Tests call the public `Distance`, `Pace`, and `Section` constructors and the `create_run` and `read_runs` use cases. Numeric validation happens during construction. Use-case tests use an in-memory storage fake for saved behavior and mocks at the `RunStorage` port for failures. Assertions check returned values, errors, and saved behavior.

## Core-step results

These measurements record the core step before SQLite storage and the model dictionary methods were added. [SQLite storage verification](sqlite-run-storage.md) records the next implementation snapshot and its constructor contract.

| Check | Result |
| --- | --- |
| `uv run pytest -q` | 71 passed. |
| `uv run pytest --cov=aweille.core --cov-branch --cov-report=term-missing` | 100% of 159 core statements and 36 branches. |
| `uv run ty check` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed. |
| `git diff --check` | Passed. |
| Built wheel import and README example | Passed in an isolated environment. |

Before this refactor, all 72 tests passed with 100% of 152 core statements and 32 branches covered. Numeric validation now has constructor tests; kilometre conversion tests were replaced by integer-metre checks. The retry, conflict, scheduling, range, and storage-failure scenarios remain covered.

A test audit reduced 85 cases to 71 with identical executed core lines and branches. Ordinary, minimum, and huge values remain covered through use cases; value-object immutability is checked in the existing saved-run test. The enum has one check of its agreed names and values. Separate invalid-input cases cover distinct rules and coercion risks rather than combinations of every field. Thirteen temporary mutations were caught, covering weakened numeric validation, mutable values, raw section fields, and retry comparisons that ignore distance or pace. Production code was unchanged during the audit.

Covered behavior:

- Positive whole-metre distances and whole-second paces, with incompatible types and booleans rejected. Exact values beyond Python's integer-to-string digit threshold remain valid.
- Immutable values and sections, enum run types, ordered repeated sections, and separate normalized notes.
- Minute-precision Montreal clock times, spring-forward gaps, fall-back ambiguity, date-only runs, and calendar endpoints.
- Identical retries, changed-field conflicts, untouched saved runs, and distinct IDs for identical content.
- Half-open range boundaries, invalid ranges, empty reads, date/time/UUID ordering, and untimed runs last.
- Both storage-failure categories, validation before saving, and no section-count or note-length cap.

## Remaining checks

The fake verifies core behavior. Real SQLite transactions, concurrency, committed snapshots, and reopening are now verified in [SQLite storage verification](sqlite-run-storage.md). HTTP parsing and errors, browser conversion and display, and application restart checks were future work at this snapshot and are now implemented in the API and browser suites.
