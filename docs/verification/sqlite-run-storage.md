# SQLite run storage verification

Verified locally on October 13, 2026, with Python 3.13.14 for [Implement SQLite run storage](https://github.com/ArnaudJalbert/aweille/issues/6). The ticket records the agreed storage interface and acceptance checks. [Testing research](../research/sqlite-storage-testing.md) explains the choice of real temporary databases.

This is a historical verification snapshot of schema version 1 and the initial `save/get` adapter, not a report on the current full suite. The current schema version 2, revisions, edit/delete operations, explicit upgrade, startup validation, and HTTP/browser checks are documented in the [README](../../README.md) and [editing/deletion contract](../design/planned-run-editing-and-deletion.md).

## Interfaces and checks

Tests use `SQLiteRunStorage(path, *, timeout=1.0)`, `save`, and `get`. Tests also exercise the public model dictionary methods, `aweille.adapters.create_database`, and the installed `aweille-init-db` command. The CLI check runs from a separate working directory. Each case uses a real file under pytest's `tmp_path`. Raw SQLite connections prepare incompatible schemas, malformed rows, locks, and rejected writes; assertions observe behavior through the public adapter. The incompatible-file check also verifies that rejected storage remains byte-for-byte unchanged.

Checks cover exact fields and notes, ordered repeated sections, targets beyond Python's integer conversion digit threshold, optional absent fields, unchanged existing IDs, half-open date ranges, committed visibility, reopening, and independent-process creation. Two spawned processes synchronize before submitting different data under one ID in a prepared database. Exactly one inserts; both receive the same winning record.

Failure cases cover unrelated schemas, non-SQLite files, malformed saved data, read-time domain failures, contention, rollback, missing parents, missing files, and unsupported text encoding. Setup tests verify successful CLI creation, refusal to overwrite existing files, and cleanup after failed initialization. A SQLite connection subclass injects failures before and after a commit, checking both rollback and retry after an uncertain successful commit. Tests do not assert SQL calls or private helper behavior.

`PlannedRun` uses the generated frozen dataclass constructor. Its `__post_init__` only validates fields. `create_run` normalizes section sequences, notes, and local times before calling the constructor directly, preserving its existing public interface. Constructor tests reject invalid and unnormalized fields; creation tests verify normalization and independence from the caller's section list. The model's public `to_dict` and class method `from_dict` own the canonical portable representation; decoding rejects noncanonical saved values. SQLite maps that representation to columns and JSON. Instance helpers use `self`; decoding helpers use `cls` where they need the model class.

## Results

| Check | Result |
| --- | --- |
| SQLite adapter and setup-command tests with `-q --durations=3` | 22 passed in 0.53 seconds; command wall time 0.533 seconds. |
| Full pytest suite with core and adapter branch coverage and `--durations=5` | 116 passed in 0.37 seconds after packaging the setup command; command wall time 0.464 seconds. |
| Core and SQLite adapter coverage | 100% of statements and branches. |
| Overall core and adapters coverage | 97% across 289 statements and 58 branches. |
| `uv run ty check` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed. |
| `git diff --check` | Passed. |
| Built wheel installed in an isolated environment | Setup command created a database from outside the checkout and refused an existing file without changing it. |

The setup CLI runs in a subprocess, so its entry code is absent from parent-process coverage. The CLI test verifies creation and refusal to overwrite an existing file. Fixtures and the rollback regression cover the creation function in the parent process.

The focused pytest run meets the agreed local target of under one second. The spawned-process case took about 0.09 seconds and the CLI case about 0.06 seconds. Deliberate lock-failure cases use a 20 ms connection timeout. The tests keep normal journal and durability settings. Timings are local observations, not CI guarantees or assertions embedded in tests.

The test audit moved canonical encoding cases to the public model methods and removed seven overlapping SQLite cases. Covered lines and branches stayed identical after that trim. Distinct transport, transaction, concurrency, and domain-failure assertions remain. The existing core matrix still checks creation normalization, retry comparison, and ordering.

The standards review found no issues. Spec review caught text-encoding error translation and loss of structured domain errors in model decoding. Both were fixed with public-interface regressions. The adapter reports safe storage errors, and the model preserves domain validation details. The full suite and static checks passed after the fixes.

The final review compared the full PR with `main` at `d926e1f`. Parallel standards and spec reviews each found zero issues. The lean pass removed redundant `ValidationError` entries where `ValueError` already covers that subclass, in the storage handler and a model rejection assertion. Both reviewers checked the cleanup. All 116 tests and required checks passed afterward, with statement and branch coverage unchanged.

## Scope

Storage assumes the database has been prepared correctly and performs no schema creation or compatibility checks. From the repository root, run `uv run aweille-init-db aweille.sqlite` once before application startup. Installed applications can use `aweille-init-db <path>` without a source checkout. The command refuses existing files and removes its new file if creation fails. Reopen tests verify ordinary persistence, not survival of power loss. Application configuration, HTTP, and browser acceptance checks followed this snapshot and are now implemented.
