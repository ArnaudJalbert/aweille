# Planned-run editing and deletion

Agreed design as of October 15, 2026, for later implementation. The application currently supports creation and range reads on schema version 1. Revisions, update/delete operations, and the upgrade command described here are not implemented yet.

This document collects the core, SQLite, HTTP, and browser implementation handoff. The [planned-run editing and deletion map](https://github.com/ArnaudJalbert/aweille/issues/17) tracks the broader effort. The original agreements are recorded in [Define planned-run update behavior](https://github.com/ArnaudJalbert/aweille/issues/18#issuecomment-6198793185), [Define concurrent writes, identity, and retries](https://github.com/ArnaudJalbert/aweille/issues/19#issuecomment-6198974288), and [Define update/delete core and SQLite contracts](https://github.com/ArnaudJalbert/aweille/issues/20#issuecomment-6200484195). The HTTP agreement is recorded in [Define the update/delete HTTP contract](https://github.com/ArnaudJalbert/aweille/issues/21); the browser agreement is recorded in [Define edit/delete browser flows and acceptance](https://github.com/ArnaudJalbert/aweille/issues/22).

## Immutable model and compatibility

Keep the frozen `PlannedRun` dataclass and add `revision: int = 1`. A revision must be a positive Python integer, without an upper limit; reject booleans, strings, floats, and other coercions. The generated constructor continues to validate already-normalized fields without changing them. Direct construction and decoding can reconstruct a saved revision, but creation and editing cannot choose a persisted revision. Storage owns its lifecycle.

Extend `to_dict()` and `from_dict()` with a required canonical `revision` field encoded as a positive decimal-digit string, such as `"1"`. Reject signs, whitespace, leading zeroes, and zero. Conversion must remain exact beyond Python's integer/string digit threshold, using the existing exact-number approach. Missing revision is invalid in the new canonical representation; the explicit database upgrade supplies it for existing storage. This is an agreed representation change. The HTTP section below specifies the transport encoding.

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

## HTTP contract

Agreed with Arnaud on October 15, 2026. This section specifies later implementation through the same API used by the browser and trainer.

### Resources and successful responses

| Method and resource | Request | Success |
| --- | --- | --- |
| `POST /v1/runs` | Existing creation JSON, without a revision. | `201` with the complete run for insertion; `200` with the current complete run for a matching normalized retry. |
| `GET /v1/runs?start=YYYY-MM-DD&end=YYYY-MM-DD` | Existing required date range. | `200` array, with unchanged half-open range and ordering semantics. |
| `GET /v1/runs/{id}` | UUID path parameter. | `200` with one complete run and its `ETag`. |
| `PATCH /v1/runs/{id}` | Partial field object and required `If-Match`. | `200` with the complete saved run and its `ETag`, including for an empty or normalized-identical edit. |
| `DELETE /v1/runs/{id}` | Required `If-Match`; no request body. | `204` with no response body or run `ETag`, after committed deletion. |

All run objects use the existing normalized response shape plus required `revision`, a canonical positive ASCII decimal-digit string matching `[1-9][0-9]*`, such as `"3"`. Keep all other fields, including nullable time and notes, present. Distances and paces retain their existing exact decimal-string encodings. Revisions have no application-imposed numeric maximum; keep them as strings in JavaScript and convert exactly in Python, including beyond its integer/string digit threshold.

Single-run GET and PATCH successes return a strong `ETag` equal to the quoted revision, such as `ETag: "3"`. Serialize a given revision's single-run JSON representation consistently. The collection has no per-run response-header validator; callers quote an item's `revision` to construct `If-Match`. POST responses need no `ETag`; a new insertion adds `Location: /v1/runs/{canonical-id}`. All `/v1/runs` resource responses, including errors, use `Cache-Control: no-store` so reloads reach the API. Conditional GET and `304` caching are outside this handoff.

### Partial field object

PATCH accepts only `planned_date`, `planned_start_time`, `run_type`, `sections`, `user_note`, and `trainer_note`. Every field is optional; `{}` is a valid edit. Preserve omission when forwarding arguments to `update_run`; never fill absent fields with `None` or request-model defaults.

- Omission retains the current field. Explicit `null` clears time or either note; it is invalid for date, run type, or sections.
- Supplying sections replaces the complete nonempty ordered list. Preserve repeated sections and use the existing section request shape and strict distance/pace encoding.
- Retain creation's UUID, date, `HH:MM`, run-type, plain-text note, exact target, and unknown-field validation. Trim notes and normalize blank notes to absence through core. Either caller may edit either note.
- The path supplies identity. Reject body `id`, `revision`, `expected_revision`, and all other unknown fields with `422`. Reject unknown query parameters on the new single-run endpoints; neither revision nor editable fields are accepted in the query.
- Core validates the complete resulting run. A date-only move that retains `02:30` on a Montreal spring-forward date fails without saving; clearing or replacing time in the same request can make the edit valid.

The body is Aweille's partial field object, not an array of JSON Patch operations or a generic JSON Merge Patch document. There is no PUT, bulk edit, section-specific resource, or deletion receipt in this contract.

Example for a live run at revision `"3"`:

```http
PATCH /v1/runs/00000000-0000-0000-0000-000000000001 HTTP/1.1
Content-Type: application/json
If-Match: "3"

{"planned_date":"2026-10-18","planned_start_time":null,"user_note":"  Keep it easy.  "}
```

If this changes normalized content, return the complete run with `revision: "4"`, `ETag: "4"`, the new date, null time, and `user_note: "Keep it easy."`; all omitted fields retain their saved values. An identical edit against current revision `"4"` returns `200` at revision `"4"`. Repeating the original request with `If-Match: "3"` returns `412` even if the fields now match.

### Required revision precondition

PATCH and DELETE require exactly one `If-Match` field containing exactly one quoted canonical revision, such as `"3"`. Header names are case-insensitive; permit ordinary HTTP whitespace around the field value, without whitespace inside the quotes. Reject repeated header fields and tag lists, including repeated identical tags. Reject wildcard `*`, weak tags such as `W/"3"`, unquoted numbers, zero, signs, leading zeroes, non-ASCII digits, and arbitrary opaque tags. This deliberately narrow API accepts one expected revision, rather than the full set of HTTP If-Match forms.

A missing header returns `428` with a safe explanation to reload and send the quoted revision. A present but empty, malformed, or unsupported header returns `422`, with location `["header", "if-match"]`. Do not use `If-Unmodified-Since` or a body/query revision as a substitute. Parse the accepted revision exactly and pass it as `expected_revision`; only storage assigns the next saved revision.

For a well-formed request, a deleted or never-existing ID returns `404`, including repeated deletion. A live run with another revision returns `412`, including an empty or normalized-identical edit. Check current state atomically with the write/no-op decision through the agreed core/storage operations. No automatic merge or substitution of a newer revision is allowed.

The use of strong validators and `412` follows [HTTP conditional requests](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.1); the missing-header outcome uses [428 Precondition Required](https://www.rfc-editor.org/rfc/rfc6585.html#section-3). Rejection of otherwise valid wildcard/list forms is this API's explicit single-revision restriction.

### Transport, validation, and safe errors

Extend the existing received-byte guard from POST to PATCH. Require `application/json` or an `application/*+json` content type, case-insensitively and allowing media-type parameters. The standardized `application/json-patch+json` and `application/merge-patch+json` formats are unsupported and return `415` on PATCH. Other accepted suffix types still carry the field object defined here.

Keep the 1 MiB (1,048,576 received bytes) body limit, including streamed bodies with absent or inaccurate Content-Length. Exactly the limit is allowed. Return `413` above it and `415` for missing/unsupported JSON content type. Malformed JSON, invalid UTF-8, non-finite constants, excessive parser nesting, absent bodies, and non-object documents return safe `422` body problems. DELETE requires no Content-Type; reject any nonempty received body with a safe `422` at `["body"]`, stopping at the first received byte rather than buffering it.

Perform transport and request parsing before invoking core. For a request passing transport checks, reject malformed path/header/query/body fields with `422`; if those fields are otherwise valid but If-Match is absent, return `428`. Do not access storage for these failures. There is no promised ordering among multiple schema problems.

After parsing, core's validation order applies: load, reject missing state, reject stale revision, then normalize and validate the resulting workout. Transport/schema failures may therefore precede missing/stale outcomes. For example, a numeric note returns `422` before core; a syntactically valid date change producing a spring-forward gap reaches core, where missing/stale state takes precedence. The final atomic storage check may still return missing/stale after core's first read.

| Outcome | Status | Body |
| --- | --- | --- |
| Invalid transport/request/domain fields | `422` | Existing `detail` problem array with only `loc`, `type`, and safe `msg`. |
| Oversized POST/PATCH body | `413` | Safe `detail` string. |
| Missing/unsupported POST/PATCH JSON content type | `415` | Safe `detail` string. |
| Missing required If-Match | `428` | `{"detail":"Reload the run and supply its quoted revision in If-Match."}` |
| Deleted or never-existing run | `404` | `{"detail":"Planned run not found."}` |
| Stale live-run revision | `412` | `{"detail":"The planned run has changed; reload it before another edit or deletion."}` |
| POST with different current content or a reserved deleted ID | `409` | `{"detail":"The ID cannot be used for this planned run."}` |
| Temporary storage unavailability | `503` | Safe `detail` string with operation-appropriate recovery guidance. |
| Other storage or unexpected operation failure | `500` | Existing safe unexpected-failure `detail` string. |

Request errors locate UUIDs at `["path", "id"]`, header problems at `["header", "if-match"]`, and body/section problems under `["body", ...]`. Preserve range-query locations under `query`. Map core editable-field errors to body paths, core identity errors to path, and expected-revision errors to the header. Invalid header problems use a stable `type: "revision_precondition"`; the message describes the required single quoted positive canonical revision without echoing the supplied value.

Error responses never include raw request values, current workout content/revision, tombstone details, SQL, paths, or driver diagnostics. A missing/deleted distinction is not exposed. Keep diagnostics in local logs. Replace the current blanket 503 instruction to retry with the same ID: reads may retry; POST may retry the same ID and payload; PATCH/DELETE callers reload and review after uncertain failures. A `500`, `503`, lost response, or timeout never proves a write rolled back.

### Reloads, retries, and compatibility

Recover through `GET /v1/runs/{id}`, even after the run moves outside the selected week. A `200` supplies current fields/revision; a `404` confirms absence. Neither proves which request produced the current state. After stale or uncertain writes, reload and review before deciding whether another write is needed. Never silently retry with the new revision.

Retrying the same expected revision can succeed if no change committed or a no-op preserved it. A committed changing edit retried at its old revision is `412`; a committed deletion retried is `404`. Delete success has no replay receipt. POST compares supplied normalized workout fields against current content, excluding revision: matching content returns `200` at the current revision; differing content returns `409`; a reserved deleted ID always returns `409`. Recreating a deleted workout requires a fresh UUID.

Keep `/v1`, existing creation inputs, `201`/`200` creation outcomes, array range reads, date/time/section encodings, ordering, and validation envelope. The required response `revision` field is an explicit additive contract change; strict response decoders must be updated alongside the browser/trainer. Creation continues rejecting unknown fields, including caller-supplied `revision`; copying a complete response into POST is not a valid creation request. The reserved-ID `409` extends creation behavior, and its message must cover both live conflicts and deleted identities. No old response shape or revision-free write compatibility mode is required for this local app. Database preparation and upgrade follow the earlier core/SQLite agreement.

### OpenAPI and public verification handoff

The later implementation must extend `/openapi.json` with the single-run GET/PATCH/DELETE paths, UUID path parameters, exact string revision in every complete response, optional PATCH properties with precise nullability and forbidden extras, and required single-tag If-Match headers on PATCH/DELETE. Revision is response-only; document that it is forbidden in write bodies. Include successful GET/PATCH `ETag`, insertion `Location`, response cache policy, the empty DELETE `204`, all applicable error statuses and safe error schemas, and examples of partial edits, clearing, no-ops, stale writes, missing preconditions, and reload recovery. Retain POST's shared `200`/`201` response model and range GET's array of that model. Do not advertise standardized patch formats or caching behavior the application does not support.

Use the existing agreed HTTP seam: `create_app(storage=...)` through TestClient and real temporary file-backed SQLite, with storage-port fault injection for failures. Inspect OpenAPI through public `GET /openapi.json`. Protect distinct behavior without duplicating core/storage checks:

- Complete creation/range/single-read/edit response consistency, revision strings and ETags, exact large revisions, Location, cache policy, UUID validation, missing reads after deletion, successful single-run reads after rescheduling, and exclusion from the old date range after a move.
- Partial-field omission versus null, normalized no-op success, ordered/repeated section replacement, forbidden identity/revision fields, and complete-result validation without partial changes.
- Missing/malformed/repeated/unsupported preconditions, current/stale edits and deletions, stale no-ops, repeated deletion, and transport/schema versus core validation precedence.
- PATCH's JSON content types, streamed byte boundary, malformed/non-object JSON and safe field paths; DELETE's body rejection. Extend shared existing transport checks rather than duplicating every POST case.
- POST retries after edits/restoration/deletion; reload after uncertain writes; safe operation-specific storage errors. Use targeted port fault injection for an intervening edit/deletion between core's load and atomic write, observing public HTTP outcomes.
- OpenAPI paths, request/response schemas, header contracts, nullable/omitted fields, success/error statuses, and examples matching observed HTTP behavior.

The browser section below records the agreed interaction and acceptance handoff for [Define edit/delete browser flows and acceptance](https://github.com/ArnaudJalbert/aweille/issues/22); this HTTP decision alone does not agree a new browser test seam.

## Browser flows and acceptance

Agreed with Arnaud on October 15, 2026. This section extends the existing compact weekly view and manual creation form for later implementation. It does not redesign their layout. The existing weekly-view and manual-creation implementations remain prerequisites for the build.

### Entry, loading, and editing

Add one accessible `Edit` link to each weekly run card, identifying its run in the accessible name. Open `/runs/{id}/edit?week=YYYY-MM-DD`, carrying the originating selected Monday. Keep deletion on the edit page, without a Delete action on weekly cards. Reuse the creation form's fields, ordered section controls, exact kilometre/pace conversion, separate plain-text notes, responsive layout, and keyboard behavior. Label this mode `Edit a planned run` with `Save changes`; keep Add run and its POST behavior intact.

The edit page is an HTML shell. Load current saved data through `GET /v1/runs/{id}`, rather than relying on the weekly card's older snapshot or reading storage in the page handler. Keep fields, Save, and Delete disabled while the initial read is pending. Prefill every field from a valid complete response, retaining canonical identity and the exact revision string separately from editable inputs. Present sections in their saved order, with repetitions intact; convert distances and paces exactly, including very large values. Null time and notes become empty form values.

An initial read failure offers Retry and return to the originating week; it never enables an empty editor. An invalid or missing run shows an explanation and a return action, without Save/Delete or automatic creation under another UUID. A failed, late, or unreadable read must not overwrite a more recent successful load. Validate any supplied origin week using the existing date/week rules and build local return URLs; do not accept arbitrary return URLs. With no usable origin, use the loaded run's week when available, otherwise the normal current-week page.

Retain the last successfully loaded saved fields and revision as the edit baseline. Save through PATCH, sending only editable fields that differ from that baseline after the existing form-to-API conversions, plus `If-Match` constructed from the baseline revision. Do not include ID or revision in the JSON. Send null when clearing time or notes; send the complete ordered section list when sections change. Leave omitted fields out, including the other caller's unchanged note. Core still owns note normalization and resulting-workout validation. Saving an unchanged or normalized-identical form may succeed without a revision increment; no new UUID is generated.

During a save, preserve and disable the editable controls and competing Save/Delete actions, announce progress, and prevent duplicate submissions. Reuse the creation form's bounded wait for a response. A request timeout stops waiting; it does not prove the server stopped processing. A valid `200` must contain the expected run identity, complete saved fields, and canonical revision. Treat an unexpected/unreadable success response as uncertain, rather than navigating on assumed saved values.

### Navigation and unsaved changes

After a confirmed successful edit, open the saved run's Monday-to-Sunday week using the returned date, including when rescheduled into another week. Fetch that week again, showing the committed normalized content in API order. After Cancel or confirmed successful deletion, return to the originating week and fetch it again. A rescheduled run disappears from its former range and appears in its destination range; it keeps its UUID.

Cancel sends no write. If editable values have changed since the last successful load, confirm before discarding them. Install the browser's ordinary unsaved-changes warning for leaving, closing, or reloading a dirty editor; use a discard confirmation for the explicit Cancel action. Browser-controlled warnings remain subject to the browser's own behavior. Leaving while a write is in flight must not claim to cancel or roll back it. Successful save/delete navigation must not trigger an obsolete discard warning.

Drafts remain in the current page's memory only. There is no autosave, local draft storage, recovery after closing the page, or automatic merging. Keep draft values and section order through validation failures and recovery attempts until the user explicitly discards them or a confirmed successful write completes the flow.

### Delete confirmation

`Delete run` opens an inline confirmation within the editor. Show the last loaded saved date and run type, rather than a possibly unsaved date/type currently typed in the form. Explain that deletion permanently removes the whole planned run and cannot be undone; if the form is dirty, also explain that its unsaved edits will be discarded. Offer `Delete permanently` and `Keep run`. Opening or cancelling this confirmation sends no write, leaves draft fields intact, and never saves them first.

Move focus to `Keep run` when the confirmation opens. While it is open, disable editing and Save so its target and revision remain the loaded baseline. `Keep run` restores editing and returns focus to `Delete run`. Confirming sends bodyless DELETE for the same UUID with the baseline `If-Match`. Do not silently reload and substitute a newer revision before deletion.

While deletion is pending, announce progress and disable competing form/confirmation actions to prevent duplicate requests. Only a confirmed `204` completes the normal deletion flow, returning to the originating week with a fresh read. Preserve safe failure explanations and the draft on errors. A stale deletion must go through the same reload recovery as a stale edit, followed by a fresh explicit deletion confirmation if the user still wants to delete the newly loaded run.

### Validation, missing state, and recovery

Reuse the existing overall status and field-error presentation. Keep all entered values after local validation or API `422` failures, attach available body/section problems to the corresponding inputs, and focus the first invalid field. Report a `413` body limit with instructions to reduce notes or sections. These definite rejected writes allow corrections and another submission using the same baseline revision; the server can still reject that revision if another caller changed the run meanwhile. Other definite request errors receive a safe explanation without silently changing identity or revision. An unexpected missing/malformed precondition (`428` or a header-related `422`) requires reload before another write, rather than asking the user to edit an HTTP header.

For `412`, keep the draft, explain that the saved run changed, and disable further Save/Delete until a successful reload. Do not automatically merge, overwrite the form, adopt the newer revision, or retry. Offer `Reload saved run` and return to the originating week. The latter uses the normal dirty-draft discard confirmation.

Use the same reload-required state after a timeout, network interruption, lost/unreadable response, or `500`/`503` during Save/Delete. Explain that the result could not be confirmed. Keep the draft for inspection/copying, and do not offer direct write retry even with the old revision. This browser policy is deliberately more conservative than the API's permitted same-revision retry behavior. Known validation errors remain correctable without this extra reload.

`Reload saved run` warns before replacing unsaved edits. Only after the user agrees does it fetch current state through single-run GET. While loading, prevent form edits and competing writes; a failed reload retains the draft, baseline, and reload-required state. A valid `200` replaces the form and baseline with current saved fields/revision, clears old field errors, and restores normal editing. It never automatically resubmits the previous draft. The user reviews the loaded values and explicitly saves or starts a new deletion confirmation if desired.

A `404` from an edit/deletion or recovery read means the run is unavailable. Retain the draft for inspection, disable writes, and offer return to the originating week. Never recreate the run or claim this particular request deleted it. After an uncertain deletion, a reload returning `404` confirms absence without identifying which caller removed it. A reload returning `200` shows current saved state; any subsequent deletion needs a new confirmation. If another caller changes it again, the next stale write repeats this recovery rather than bypassing the precondition.

### Refresh and accessibility

Trainer/other-tab changes appear through manual page reload or week navigation. Returning from the editor, including browser Back and a restored page, fetches the selected week again instead of retaining a cached stale card. Do not poll, add background refresh, or replace the open editor's values on focus. Keep the selected week stable across Monday, as today.

Preserve existing loading/error behavior: clear old weekly results during a new read, offer Retry for the selected week, retain navigation, and prevent late reads from replacing a newer selection. A failed refresh after a successful write must show the read failure rather than resurrect stale cards or resend the write. Keep existing Add run, JavaScript-unavailable messages, plain-text note rendering, exact formatting, phone layout, and keyboard access. Distinguish initial loading, Save/Delete progress, validation failure, stale state, uncertain result, and missing state in accessible status messages. Keep visible focus meaningful as controls appear/disappear; after a recovery load, focus the editor heading or status explaining the loaded state.

### Public browser verification handoff

Use the existing public browser and HTTP seams: Playwright interactions with the rendered pages against real Uvicorn and temporary file-backed SQLite; the shared API represents trainer/other-tab actions. Restart the server against the same database for persistence checks. Inject HTTP read/write failures and lost responses at the HTTP boundary, including letting a real write commit before hiding its response. Do not assert private JavaScript helpers, internal call sequences, or raw database state for normal behavior.

Extend existing scenarios where they already cover the behavior. Protect these distinct acceptance cases:

- A trainer/API-created run opens through its card's Edit link with current fields, both notes, ordered repeated sections, and exact large targets. A direct edit link works; initial loading/failure/missing-state controls cannot submit a blank form.
- Edit only one field and observe that omitted fields and identity survive through API reload and the weekly view. Check clearing time/notes, section reorder/replacement, normalized no-op behavior, and unchanged revisions for no-ops through public responses.
- Save a date change across weeks, see the run in the destination, and read the former week without it. Cancel returns to origin without a write. Returning through browser Back refetches the selected week, including when a restored page would otherwise show stale cards.
- Opening/abandoning delete confirmation preserves the saved run and draft. Confirming deletion removes the run from browser/API reads and returns to origin. Exercise a trainer change or deletion after the editor loaded: stale actions cannot overwrite/delete newer state, and missing actions cannot recreate it.
- Stale edit/delete retains the draft and blocks writes. Cancelling reload preserves the draft. A failed reload also preserves it and remains blocked; an accepted successful reload replaces it with current state and requires a new explicit action. Include a trainer note edit competing with a browser user-note edit to protect whole-run revision semantics.
- Lost responses after committed and uncommitted edits/deletions, server failures, and unreadable successes retain the draft and require GET recovery rather than write retry. Recovery reflects current state or absence without claiming who committed it. A no-op with a lost response follows the same browser recovery policy.
- Validation and oversized-request errors preserve values and meaningful field/overall errors, allowing correction. Include the Montreal spring-forward retained-time error and correction in one edit; preserve existing fall-back behavior. Slow initial reads and writes expose progress and prevent duplicate/competing actions.
- Unsaved Cancel/reload warnings respect Keep/Discard, and successful write navigation avoids false discard warnings. Delete confirmation and recovery actions are keyboard accessible with visible focus; phone layout remains usable. Notes stay plain text, including loaded and retained draft values.
- After stopping and restarting against the same file, edited fields/revisions and deleted absence remain visible through the browser/API; a POST under the reserved deleted UUID still conflicts. Preserve existing creation retry, range ordering, exact formatting, selected-week navigation, failure recovery, and JavaScript-unavailable coverage.

These browser checks complement the core/storage concurrency and migration checks and the HTTP/OpenAPI checks already agreed above; they do not duplicate every rule at every seam. Skipping, results, undo, batch editing, drag-to-reschedule, live collaboration, draft persistence, and a new visual design remain outside this handoff.

## Handoff

The core, SQLite, HTTP, and browser contracts and their public test seams are agreed. The handoff above resolves [Define the update/delete HTTP contract](https://github.com/ArnaudJalbert/aweille/issues/21) and [Define edit/delete browser flows and acceptance](https://github.com/ArnaudJalbert/aweille/issues/22), completing the [planned-run editing and deletion map](https://github.com/ArnaudJalbert/aweille/issues/17). Application implementation follows this planning effort.
