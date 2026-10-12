# Planned-run core verification

Verified locally on October 12, 2026, for [issue #5](https://github.com/ArnaudJalbert/aweille/issues/5). The [grilling report](https://github.com/ArnaudJalbert/aweille/issues/5#issuecomment-6128315787) records the agreed interface and tools.

## Test seam

Tests call the public `create_run` and `read_runs` functions. A dictionary-backed storage fake retains runs and returns range results in unspecified order. Storage-failure tests use mocks at the storage port. Tests observe returned values and errors, without inspecting private core collaborators or asserting call sequences.

## Results

The current full suite passed with Python 3.13.14. The original 90-case suite also passed during implementation with Python 3.14.7. Development tools are pinned in the shared `uv.lock`.

| Check | Result |
| --- | --- |
| `uv sync --locked --all-packages` | Passed. One workspace member, no runtime dependencies. |
| `uv run pytest packages/aweille/tests/use_cases/test_create_run.py -q` | 64 passed. |
| `uv run pytest packages/aweille/tests/use_cases/test_read_runs.py -q` | 8 passed. |
| `uv run pytest -q` | 72 passed. |
| `uv run ty check` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed. |
| Temporary coverage.py measurement | 100% of core statements and branches after the workflow refactor. |
| `git diff --check` | Passed. |
| `uv build --package aweille --out-dir /tmp/aweille-core-layout-dist` | Built a source distribution and wheel. |
| Isolated installation of the built wheel | Package and public core imported with no runtime dependencies. |

Covered behavior:

- The representative interval run, including repeated ordered sections and separate notes.
- Exact whole-metre distances and whole-second paces, including values beyond Decimal context precision and Python's integer-to-string digit threshold.
- Invalid input types, non-finite or nonpositive distances, fractional metres, invalid paces, missing sections, invalid run types, and invalid notes.
- Minute precision, naive local times, Montreal spring-forward gaps, allowed fall-back ambiguity, date-only runs, and calendar endpoints.
- Blank-note normalization and preservation of internal spacing and line breaks.
- Normalized retries, conflicts for changed fields or section order, immutable saved values, and distinct IDs for identical content.
- Half-open range boundaries, invalid ranges, empty reads, date/time/UUID ordering, and untimed runs last.
- Both storage-failure categories and validation before accessing unavailable storage.
- No core section-count or note-length cap.

## Limits

The fake verifies core behavior, not real persistence guarantees. SQLite transactions, concurrency, committed snapshots, HTTP parsing and errors, browser behavior, and restart persistence remain for their later implementation steps.

## Test necessity audit

The original suite had 18 test functions expanded into 90 parametrized cases. The audit removed 18 repeated cases, leaving 72 cases in the same 18 functions. Production code did not change.

- Removed repeated incompatible-type examples after retaining cases for each field, meaningful coercion risk, and validation path.
- Kept zero and negative numbers, fractional metres, NaN, signaling NaN, infinity, integer versus floating-point values, boolean pace, and exact-value limits.
- Replaced three examples within the spring-forward gap with its first and last minute, retaining valid times immediately before and after it.
- Kept the fall-back `fold=1` input and its retry with `fold=0` in one case. The separate `fold=0` case repeated that check.
- Removed the summer scheduling example because the representative October run uses the same daylight-saving offset. Winter scheduling and calendar endpoints remain.
- Changed the distance and pace conflict cases to alter one section value while preserving section count and all other fields. Their original inputs also changed the section count, which could hide a broken value comparison.

Before the file-layout refactor, coverage measured 100% of core statements and branches before and after pruning: 114 statements and 32 branches, with identical executed lines and branches. Coverage supports the audit; the contract scenarios determine which cases stay.

A mutation check simulated retry comparison ignoring section distance, in an isolated process without editing production code. The original conflict tests passed with that bug; the strengthened distance-conflict case failed as intended. This check used the existing public test seam.

To reproduce coverage without adding a project dependency:

```sh
COVERAGE_FILE=/tmp/aweille-core.coverage uv run --with coverage \
  python -m coverage run --branch --source=aweille.core -m pytest -q
COVERAGE_FILE=/tmp/aweille-core.coverage uv run --with coverage \
  python -m coverage report -m
```

## File organization checks

Use cases, models, and errors now live in separate named modules. Shared date validation and error construction also have their own modules. Test files mirror the use cases, and `conftest.py` registers the separate fixture modules. The [file organization rule](../../AGENTS.md#file-organization) records this convention.

The split retains all 72 cases: 64 for creation and eight for range reads. The two storage-failure categories remain checked for each use case. Invalid-range checks now also establish that validation happens before unavailable storage is accessed.

Coverage after the move is 100% of 141 core statements and 32 branches. The statement count increased because components now import their dependencies in their own modules. The rebuilt wheel imports both named use-case modules and the existing `aweille.core` public exports without runtime dependencies.

## Workflow readability checks

The public create function now normalizes a run, asks storage to insert it, checks any existing run for retry conflicts, and returns the committed outcome. Its private helpers handle run construction, ordered sections, exact distance conversion, pace validation, and retry comparison. The read function validates its range, fetches runs, and applies its named sort key.

The same 72 tests pass through the public functions. Validation order, safe errors, normalized values, storage outcomes, and scheduling order are preserved. Coverage is 100% of 155 core statements and 32 branches; ty and Ruff also pass. The [function structure rule](../../AGENTS.md#function-structure) records the agreed style.
