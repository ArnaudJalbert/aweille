# SQLite run storage verification

Verified locally on October 13, 2026, with Python 3.13.14 for [Implement SQLite run storage](https://github.com/ArnaudJalbert/aweille/issues/6). The ticket records the agreed storage interface and acceptance checks. [Testing research](../research/sqlite-storage-testing.md) explains the choice of real temporary databases.

## Interfaces and checks

Tests use `SQLiteRunStorage(path, *, timeout=1.0)`, `save`, and `get`. Tests also exercise the public model dictionary methods and the database setup function and CLI. Each case uses a real file under pytest's `tmp_path`. Raw SQLite connections prepare incompatible schemas, malformed rows, locks, and rejected writes; assertions observe behavior through the public adapter. The incompatible-file check also verifies that rejected storage remains byte-for-byte unchanged.

Checks cover exact fields and notes, ordered repeated sections, targets beyond Python's integer conversion digit threshold, optional absent fields, unchanged existing IDs, half-open date ranges, committed visibility, reopening, and independent-process creation. Two spawned processes synchronize before submitting different data under one ID in a prepared database. Exactly one inserts; both receive the same winning record.

Failure cases cover unrelated schemas, non-SQLite files, malformed saved data, read-time domain failures, contention, rollback, missing parents, missing files, and unsupported text encoding. Setup tests verify successful CLI creation, refusal to overwrite existing files, and cleanup after failed initialization. A SQLite connection subclass injects failures before and after a commit, checking both rollback and retry after an uncertain successful commit. Tests do not assert SQL calls or private helper behavior.

`PlannedRun` uses the generated frozen dataclass constructor and a validation-only `__post_init__`. Direct construction requires normalized values. `create_run` normalizes inputs before construction, preserving its existing public interface. The model's public `to_dict` and static `from_dict` own the canonical portable representation. SQLite only maps that representation to columns and JSON. Pure supporting helpers are static methods on their owning classes.

## Results

| Check | Result |
| --- | --- |
| All adapter tests with `-q --durations=3` | 22 passed in 0.25 seconds; command wall time 0.319 seconds. |
| Full pytest suite with branch coverage and `--durations=5` | 112 passed in 0.36 seconds; command wall time 0.397 seconds. |
| Core and SQLite adapter coverage | 100% of statements and branches. |
| Overall core and adapters coverage | 97% across 296 statements and 58 branches. |
| `uv run ty check` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed. |
| `git diff --check` | Passed. |

The setup CLI runs in a subprocess, so its entry code is absent from parent-process coverage. The CLI test verifies creation and refusal to overwrite an existing file. Fixtures and the rollback regression cover the creation function in the parent process.

The focused pytest run meets the agreed local target of under one second. The spawned-process case took about 0.09 seconds and the CLI case about 0.06 seconds. Deliberate lock-failure cases use a 20 ms connection timeout. The tests keep normal journal and durability settings. Timings are local observations, not CI guarantees or assertions embedded in tests.

The test audit moved canonical encoding cases to the public model methods and removed seven overlapping SQLite cases. Covered lines and branches stayed identical after that trim. Distinct transport, transaction, concurrency, and domain-failure assertions remain. The existing core matrix still checks creation normalization, retry comparison, and ordering.

The standards review found no issues. Spec review caught text-encoding error translation and loss of structured domain errors in model decoding. Both were fixed with public-interface regressions. The adapter reports safe storage errors, and the model preserves domain validation details. The full suite and static checks passed after the fixes.

## Scope

Storage assumes the database has been prepared correctly and performs no schema creation or compatibility checks. Run `uv run python -m aweille.adapters.create_database aweille.sqlite` once before application startup. The setup script refuses existing files and removes its new file if creation fails. Reopen tests verify ordinary persistence, not survival of power loss. Application configuration, HTTP, and browser acceptance checks remain in later tickets.
