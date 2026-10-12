# Planned-run core verification

Verified locally on October 12, 2026, for [issue #5](https://github.com/ArnaudJalbert/aweille/issues/5). The [grilling report](https://github.com/ArnaudJalbert/aweille/issues/5#issuecomment-6128315787) records the agreed interface and tools.

## Test seam

Tests call the public `create_run` and `read_runs` functions. A dictionary-backed storage fake retains runs and returns range results in unspecified order. Storage-failure tests use mocks at the storage port. Tests observe returned values and errors, without inspecting private core collaborators or asserting call sequences.

## Results

The full suite passed with Python 3.13.14. Focused checks also passed during implementation with Python 3.14.7. Development tools are pinned in the shared `uv.lock`.

| Check | Result |
| --- | --- |
| `uv sync --locked --all-packages` | Passed. One workspace member, no runtime dependencies. |
| `uv run pytest packages/aweille/tests/test_planned_runs.py -q` | 90 passed. |
| `uv run pytest -q` | 90 passed. |
| `uv run ty check` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed. |
| `git diff --check` | Passed. |
| `uv build --package aweille --out-dir /tmp/aweille-core-dist` | Built a source distribution and wheel. |
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
