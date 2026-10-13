# SQLite run storage verification

Verified locally on October 13, 2026, with Python 3.13.14 for [Implement SQLite run storage](https://github.com/ArnaudJalbert/aweille/issues/6). The ticket records the agreed storage interface and acceptance checks. [Testing research](../research/sqlite-storage-testing.md) explains the choice of real temporary databases.

## Interfaces and checks

Tests use `SQLiteRunStorage(path, *, timeout=1.0)`, `save`, and `get`. Each case uses a real file under pytest's `tmp_path`. Raw SQLite connections prepare incompatible schemas, malformed rows, locks, and rejected writes; assertions observe behavior through the public adapter. The incompatible-file check also verifies that rejected storage remains byte-for-byte unchanged.

Checks cover exact fields and notes, ordered repeated sections, targets beyond Python's integer conversion digit threshold, optional absent fields, unchanged existing IDs, half-open date ranges, committed visibility, reopening, and independent-process creation. Two spawned processes synchronize before opening the same absent file and submit different data under one ID. Exactly one inserts; both receive the same winning record.

Failure cases cover unsupported versions, missing indexes, unrelated schemas, non-SQLite files, malformed saved data, read-time domain failures, contention, rollback, missing parents, missing files, and unsupported text encoding. A SQLite connection subclass injects failures before and after a commit, checking both rollback and retry after an uncertain successful commit. Tests do not assert SQL calls or private helper behavior.

`PlannedRun` now owns the existing field validation and normalization during construction, as agreed during implementation. `create_run` delegates to that constructor; SQLite reconstructs domain objects without importing private core helpers or owning business rules. Existing public exports and use-case call signatures remain unchanged. The existing core test matrix still protects validation, normalization, retry comparison, and ordering.

## Results

| Check | Result |
| --- | --- |
| Focused SQLite file with `-q --durations=5` | 30 passed in 0.25 seconds; command wall time 0.347 seconds. |
| Full pytest suite with branch coverage and `--durations=5` | 101 passed in 0.33 seconds; command wall time 0.457 seconds. |
| Core and adapter coverage | 100% of 245 statements and 52 branches. |
| `uv run ty check` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed. |
| `git diff --check` | Passed. |

The focused pytest run meets the agreed local target of under one second. Spawned-process creation took about 0.09 seconds; each deliberate lock-failure case took about 0.03 seconds with a 20 ms connection timeout. The tests keep normal journal and durability settings. Timings are local observations, not CI guarantees or assertions embedded in tests.

The test audit kept distinct transport, schema, transaction, and concurrency failures without repeating the core's full domain-validation matrix. Coverage remained complete after moving normalization into `PlannedRun`. Coverage supports this audit but does not replace the behavioral assertions.

The standards review found no issues. The spec review found a raw text-encoding error at the SQLite seam. The adapter now translates it to a safe `StorageFailure`; a regression check verifies unchanged storage and a successful subsequent write. The affected checks and full suite passed after the fix.

## Scope

Storage accepts only its identified initial schema and rejects incompatible files without migrations. Reopen tests verify ordinary persistence, not survival of power loss. Application configuration, HTTP, and browser acceptance checks remain in later tickets.
