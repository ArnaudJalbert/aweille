# SQLite storage testing

Researched on October 13, 2026, for [issue #6](https://github.com/ArnaudJalbert/aweille/issues/6).

## Recommendation

Use real SQLite files under pytest's `tmp_path` for the adapter's public `save` and `get` tests. Prepare each file through the separate database-creation script. Check that script's public function and command-line entry point separately. Keep the existing core fake and port mocks. Use targeted driver fault injection only for failures that are hard to reproduce reliably.

This is our recommendation from the facts below, not a universal testing rule stated by Python or SQLite. It also follows this repository's [contributor workflow](../../CONTRIBUTING.md#tests), which separates core tests from real adapter checks. No extra database or mocking framework is needed.

## Why real SQLite

Python's `sqlite3` is embedded and requires no separate server. Its own tutorial checks saved data by closing a file connection, opening another, and reading it back. A small temporary database exercises actual SQL, constraints, serialization, and commit behavior. [Python sqlite3 documentation](https://docs.python.org/3.13/library/sqlite3.html#tutorial)

`unittest.mock` can supply configured return values and raise exceptions through `side_effect`; autospec checks interface signatures. Our inference is that replacing the driver verifies how the adapter handles those configured outcomes, but cannot establish that its SQL works or that writes actually commit. [Python mock documentation](https://docs.python.org/3.13/library/unittest.mock.html#quick-guide)

Separate SQLite connections normally see committed transactions only, and SQLite permits one writer at a time. Testing those properties through the adapter can catch missing transactions or premature success reports. One connection can see its own uncommitted writes, so reading back on the writer alone does not prove commitment. [SQLite isolation documentation](https://www.sqlite.org/isolation.html)

Plain `:memory:` is real SQLite, but its database disappears on close and each connection gets its own database. Shared in-memory databases are possible with URI configuration; they still disappear when the last connection closes. [SQLite in-memory documentation](https://www.sqlite.org/inmemorydb.html)

SQLite discourages shared-cache mode and documents different locking semantics. We therefore recommend file-backed databases for reopening and contention checks rather than introducing shared-cache memory just for tests. [SQLite shared-cache documentation](https://www.sqlite.org/sharedcache.html#use_of_shared_cache_is_discouraged)

## Keeping the checks fast

`tmp_path` supplies a unique directory per test function. Use a fresh, small database there and close connections during fixture teardown. Share setup code rather than a writable database across tests. Pytest supports function-scoped fixtures and teardown after `yield`. [Pytest temporary files](https://docs.pytest.org/en/stable/how-to/tmp_path.html#the-tmp-path-fixture), [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html#teardown-cleanup-aka-fixture-finalization)

Keep adapter cases focused on round trips, range boundaries, unchanged existing IDs, commitment, reopening, unreadable files, concurrency, and error translation. Model tests cover dictionary encoding and decoding. The existing [core verification](../verification/planned-run-core.md) already covers business validation, retry comparison, conflicts, and sorting. Avoid repeating that matrix against SQLite. The implementation review moved schema creation out of storage; runtime schema compatibility checks are no longer part of the adapter.

Use separate connections and events or barriers for concurrent cases, with bounded waits and worker cleanup. Python provides these synchronization primitives. Our recommendation is to avoid sleeps and repeated races, which add time without proving the intended ordering. [Python threading documentation](https://docs.python.org/3.13/library/threading.html#event-objects)

A locked write can wait five seconds under Python's default connection timeout. Configure a deliberately short timeout for the one test that checks lock failure, through an agreed configuration seam. This need not alter production settings. Close every connection explicitly; the connection context manager handles transactions but does not close the connection. [Python connection options](https://docs.python.org/3.13/library/sqlite3.html#sqlite3.connect), [connection context manager](https://docs.python.org/3.13/library/sqlite3.html#how-to-use-the-connection-context-manager)

Keep production journal and durability settings in representative tests. Do not turn synchronization off to improve timings. Measure the affected file and whole suite with pytest's `--durations` option and elapsed wall time before claiming that the finished adapter suite meets a speed budget. [Pytest duration reporting](https://docs.pytest.org/en/stable/how-to/usage.html#profiling-test-execution-duration)

## Local measurements

Measured on October 13, 2026, on Darwin with Python 3.13.14 and SQLite 3.53.1. The synthetic workloads used ordinary files in the OS temporary directory, SQLite's default DELETE journal mode, and `synchronous=FULL`. The measurements below are local observations, not claims from the linked documentation.

| Check | Samples | Median | Tail observation | Total |
| --- | --- | --- | --- | --- |
| Create schema, separately save and commit seven runs, reopen, range read | 50 | 2.028 ms | p95 2.665 ms | 107.503 ms |
| Two connections concurrently insert the same ID, read, commit, verify one saved row | 10 | 1.528 ms | Maximum 7.429 ms | 21.207 ms |
| Held write lock, contender with a 20 ms timeout reports `SQLITE_BUSY` | 5 | 24.957 ms | Maximum 25.229 ms | 124.693 ms |

The first workload created a table for all seven planned-run fields and a date index. Each of seven inserts opened its own connection, committed, and closed before a final connection checked the range results. Sections used JSON with ordered, repeated entries and decimal-digit strings for metres and seconds per kilometre. Its p95 uses the nearest-rank method. The concurrency workload used two worker threads, separate connections, a barrier, and `INSERT ... ON CONFLICT DO NOTHING`; its timing included worker creation and cleanup but excluded schema setup. The lock workload held `BEGIN IMMEDIATE` until the contender failed, then cleaned up without sleeps.

The existing core suite passed all 71 tests in 0.07 seconds according to `uv run pytest --durations=5`. The command took about 0.33 seconds externally, including uv build/startup overhead. Keep pytest-reported duration separate from command wall time when comparing results.

The maintainer agreed to a target of under one second for the focused adapter pytest run on this machine during the October 13 grilling session. Measure the implemented tests against it and report command wall time separately from pytest duration. Record full-suite timing too. This local target is not a CI guarantee and should not be enforced with brittle per-test timing assertions.

## Measurement limits

These measurements preceded the adapter implementation. The direct SQLite workloads did not use the eventual adapter, exercise core decoding, or cover every accepted value size. Their timings show local overhead and do not establish a CI timing guarantee. The implemented checks are recorded separately in [SQLite storage verification](../verification/sqlite-run-storage.md). Persistence checks after a clean reopen also do not establish power-loss durability.
