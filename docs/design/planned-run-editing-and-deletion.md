# Planned-run editing and deletion

Agreed design as of October 15, 2026, for later implementation. The application currently supports creation and range reads on schema version 1. Revisions, update/delete operations, and the upgrade command described here are not implemented yet.

This document collects the core and SQLite implementation handoff. The [planned-run editing and deletion map](https://github.com/ArnaudJalbert/aweille/issues/17) tracks the broader effort. The original agreements are recorded in [Define planned-run update behavior](https://github.com/ArnaudJalbert/aweille/issues/18#issuecomment-6198793185), [Define concurrent writes, identity, and retries](https://github.com/ArnaudJalbert/aweille/issues/19#issuecomment-6198974288), and [Define update/delete core and SQLite contracts](https://github.com/ArnaudJalbert/aweille/issues/20#issuecomment-6200484195). HTTP and browser contracts remain separate decisions.

## Immutable model and compatibility

Keep the frozen `PlannedRun` dataclass and add `revision: int = 1`. A revision must be a positive Python integer, without an upper limit; reject booleans, strings, floats, and other coercions. The generated constructor continues to validate already-normalized fields without changing them. Direct construction and decoding can reconstruct a saved revision, but creation and editing cannot choose a persisted revision. Storage owns its lifecycle.

Extend `to_dict()` and `from_dict()` with a required canonical `revision` field encoded as a positive decimal-digit string, such as `"1"`. Reject signs, whitespace, leading zeroes, and zero. Conversion must remain exact beyond Python's integer/string digit threshold, using the existing exact-number approach. Missing revision is invalid in the new canonical representation; the explicit database upgrade supplies it for existing storage. This is an agreed representation change. HTTP revision encoding remains a separate decision.

Keep `create_run` returning `(run, inserted)` and `read_runs` returning runs with the existing range and ordering semantics. Returned runs now include their persisted revision. Creation starts at 1. Changed normalized workout content increments the stored revision by one; an empty or normalized-identical edit keeps it. Restoring old content increments the revision rather than restoring an old revision.

Creation retries compare normalized workout fields, excluding revision. Matching current content returns the current run and revision with `inserted=False`; differing content raises `RunConflict`. Any creation using a deleted, reserved UUID raises `RunConflict`. Do not retain creation snapshots or operation receipts.

## Public core use cases

Export these additions from `aweille.core`, alongside the existing models, errors, storage port, and use cases:

```python
read_run(storage, *, id) -> PlannedRun

update_run(
    storage,
    *,
    id,
    expected_revision,
    planned_date=UNSET,
    planned_start_time=UNSET,
    run_type=UNSET,
    sections=UNSET,
    user_note=UNSET,
    trainer_note=UNSET,
) -> PlannedRun

delete_run(storage, *, id, expected_revision) -> None
```

`id` is a UUID. `expected_revision` is a required positive Python integer with the same strict type rules as a saved revision. It has no default. `UNSET` is a dedicated omission sentinel, distinct from `None`; no separate changes object is needed. Editable inputs retain the types accepted by creation: dates, naive minute-precision local times, `RunType`, ordered `Sequence[Section]`, and optional plain-text notes. There is no editable ID or saved-revision argument.

Omitted fields retain their saved values. `None` clears time or either note, but is invalid for date, run type, or sections. Supplying sections replaces the entire ordered list, which must remain nonempty. Normalize sections, notes, and time using the creation rules, without mutating the saved immutable run or the caller's section sequence. Both callers may edit either note; omission preserves the other note.

Core validates the complete proposed run, including a retained time on a changed Montreal date. A date-only move of a 02:30 run onto the spring-forward day fails. Clearing or replacing the time in that same edit can make the result valid. Invalid combined changes save nothing. Keep existing minute precision, fall-back semantics, section ordering/repetitions, and exact distance/pace rules.

## Errors and validation order

- `ValidationError`: invalid UUID, revision value, editable input, or resulting run, with existing safe structured problems. Missing required Python arguments are rejected by the required function signature; transport parsing belongs to the HTTP ticket.
- `RunNotFound`: single-run read, edit, or deletion targets a deleted or never-existing run. Those two cases are indistinguishable. Editing never creates a run; repeated deletion reports missing.
- `RunRevisionConflict`: a live run's revision differs from the expected revision, including for an empty or normalized-identical edit. Reload before deciding whether to submit another change.
- `RunConflict`: creation conflicts with current workout content or a reserved deleted identity.
- `StorageUnavailable` and `StorageFailure`: preserve the existing temporary/unexpected failure categories and safe messages. SQL, paths, stored values, and driver diagnostics do not escape through public errors.

For an edit, first validate ID and expected revision before storage access. Load the current run, reject missing state, then reject a stale revision. Only then normalize and validate the complete proposed result. Thus an already-stale edit with malformed editable fields reports stale; an invalid expected-revision value reports validation. Corrupt persisted data is a storage failure, not a user validation error.

After validation, storage must recheck existence and expected revision atomically with its replacement/no-op decision. A competing edit or deletion between the core load and replacement can therefore change the final error to stale or missing. Do not automatically reload and reapply with a newer revision. Single-run reads validate ID before loading; deletion validates ID/revision and delegates the atomic check and removal to storage.

## Core-owned storage port

Keep the existing synchronous `RunStorage.save(run)` and range `get(start, end)` operations and add:

```python
load(id: UUID) -> PlannedRun | None
replace(run: PlannedRun, *, expected_revision: int) -> PlannedRun
delete(id: UUID, *, expected_revision: int) -> None
```

`load` returns a normalized immutable run from committed state, or `None` for either kind of missing ID. Core converts absence to `RunNotFound`.

`replace` accepts the complete validated, normalized candidate produced by core. Within one write transaction it loads the saved run, raises `RunNotFound` if absent, and raises `RunRevisionConflict` if the expected revision differs. Check the revision even when content matches. Compare workout content excluding revision: identical content returns the current run unchanged; changed content is stored with the current revision plus one. Storage assigns the resulting revision from saved state, never from a caller-chosen candidate revision. Return success only after commit. This operation never inserts a missing run.

`delete` checks existence and revision in the same transaction that removes all workout content and reserves its UUID. A reserved-ID table contains only IDs, without notes, sections, snapshots, previous revisions, or operation results. Reservation survives restart forever. Success returns `None` only after commit.

`save` must atomically check the reserved-ID table and insert a missing live run at revision 1, or return the current live run unchanged for core's retry comparison. A reserved ID raises `RunConflict`. Preserve `(stored_run, inserted)` and committed insertion semantics. Range `get` keeps its committed-snapshot contract and excludes deleted runs.

## Atomic SQLite operations

Store canonical revision strings in a non-null TEXT column. Compare canonical revisions for equality and increment with exact Python arithmetic. Keep the existing planned-date index. Use an ID-only table for deleted UUIDs.

Use SQLite write transactions, such as `BEGIN IMMEDIATE`, around each save, conditional replacement, and conditional deletion. Acquire the writer lock before reading the state used for the decision. This serializes competing writers across application processes, including no-op decisions and POSTs racing deletion. Core supplies no callback to run inside storage transactions. Keep reads as committed snapshots and close connections after each operation. Retain bounded SQLite lock waits and no adapter retry loop.

Two changing edits against one revision allow one winner; the other is stale. An edit before deletion makes the deletion stale. Deletion before an edit or another deletion makes the later request missing. A no-op preserves its revision, allowing another request using that revision to succeed. Deletion and ID reservation commit together, so a delayed POST cannot resurrect the run.

Failure before commit rolls back the whole operation, including reservation. Failure after a possible commit may leave the outcome uncertain. Preserve safe storage failure categories; never claim such a failure proves rollback. Recovery follows the earlier concurrency agreement: reload, review, and do not automatically replace an expected revision. A committed no-op may be retried while its revision remains current; a committed changing edit retried with its old revision is stale, and a committed deletion retried is missing.

## Prepared databases and explicit upgrade

Add public `upgrade_database(path)` and installed `aweille-upgrade-db <path>`. Run the upgrade with the application stopped. Open an existing file without creating or replacing it. Recognize Aweille's application ID (`0x41574549`), schema version, expected schema, and valid saved data; do not treat an arbitrary file with a version marker as compatible.

Upgrade recognized version-1 storage in one transaction: preserve every workout, ID, section, date/time, and note; initialize all revisions to `"1"`; add the ID-only deleted-run table; preserve the date index; and advance `user_version` to 2 only with the successful upgrade. Validate before accepting the result. A valid version-2 database is an unchanged success. Reject missing, unrelated, malformed, or unsupported databases without repair, replacement, or partial migration. A failed upgrade leaves the original schema, data, and version intact.

New database initialization creates version 2 and keeps its existing refusal to overwrite an existing path. Application startup checks compatibility and reports when an explicit upgrade is required; it does not change schema. Adapter construction continues to retain settings without opening the database. Operations on incompatible schemas raise safe `StorageFailure`; retain `StorageUnavailable` for temporary access/locking faults. The upgrade function uses the same safe failure categories, and the CLI reports failure with a nonzero exit status without leaking diagnostics.

## Agreed test seams and meaningful checks

Use public model constructors/dictionary methods and `create_run`, `read_run`, `read_runs`, `update_run`, and `delete_run` for core checks. Extend the existing small in-memory storage fake for normal saved behavior; inject storage-port failures with mocks. Assert returned values, public errors, and saved behavior, not private helpers or call sequences.

Use public SQLite storage methods against real temporary files, reopening and independent processes for integration checks. Use the public upgrade function and installed CLI for migration checks. Raw SQLite may arrange corrupt data, locks, incompatible schemas, or rejected writes; targeted driver fault injection may arrange failures before/after commit. Observe results through the agreed public seams, with file/schema comparisons when verifying rejected or failed upgrades leave storage unchanged.

Protect these distinct cases without duplicating existing assertions:

- Strict revision construction and canonical round-trip, including exact revisions beyond SQLite integer limits and Python's conversion threshold; immutable models and unchanged create/read return shapes.
- Partial edits retaining omitted fields; explicit clearing and blank-note normalization; complete ordered-section replacement with repetitions; invalid empty sections and required-field nulls.
- Complete-result validation and all-or-nothing edits, especially a retained time on a spring-forward date versus clearing/replacing that time; existing fall-back rules remain intact.
- Creation at revision 1, changing edits, restoring earlier content, empty/normalized no-ops, stale no-ops, missing operations, invalid ID/revision values, and the agreed validation/error order.
- POST retries after edits, restoration, and deletion; matching current content returns its current revision; deleted IDs never reappear. Range reads omit deleted runs.
- Independent-process edit/edit, edit/delete, delete/delete, no-op/change, and POST/delete races. Assert valid serialized outcomes and no lost update or resurrection, without assuming which process wins.
- Reopen persistence of revisions and reservations; transaction rollback; uncertain committed edits, no-ops, and deletions; safe storage failures and continued usability after faults.
- Upgrade preservation and initial revisions; valid-v2 idempotence; missing/unrelated/malformed/unsupported rejection; rollback of a failed upgrade; new-v2 initialization; startup compatibility rejection without migration; and CLI behavior.

## Handoff

The core/SQLite contract and public test seams are agreed. [Define the update/delete HTTP contract](https://github.com/ArnaudJalbert/aweille/issues/21) still owns HTTP methods, revision transport, response shapes, reload access, and status codes. [Define edit/delete browser flows and acceptance](https://github.com/ArnaudJalbert/aweille/issues/22) still owns browser behavior. Application implementation follows this planning effort.
