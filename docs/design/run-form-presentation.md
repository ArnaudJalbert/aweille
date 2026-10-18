# Run-form, deletion, and recovery presentation

Arnaud approved the complete presentation through [Define run-form, deletion, and recovery presentations](https://github.com/ArnaudJalbert/aweille/issues/46#issuecomment-6243248791). This is the design handoff for the current run-only app. The browser implementation follows this decision; [integrated verification](../verification/redesign-acceptance.md) records evidence and remaining manual acceptance.

## Form and actions

Create/edit replaces the schedule content area beside the [approved sidebar](sidebar-integration.md). Put the menu beside the form heading. Keep the field order: planned date and optional start time, run type, ordered sections, then separate optional personal and trainer notes. Persistent labels include units; explain that fields are required unless marked optional. Draft text stays readable and available through recoverable failures.

Add section focuses the new distance input. Remove cannot remove the last section. Named up/down controls preserve order, disable at boundaries, and retain focus in the affected row. Preserve exact kilometre/pace conversion, including large values and repeated sections.

A compact sticky footer keeps Cancel and Delete run on the left, with Save run or Save changes on the right. Delete run is a solid red button immediately after Cancel and appears only for a loaded existing run. The footer remains available while scrolling long notes and many sections; give fields clearance above it. Preserve 44px targets and a single-row footer at 320px.

Buttons match Add run: IBM Plex Sans, 13px, weight 500, 20px line height. This applies to footer, confirmation, section, and recovery actions. Main actions use light green `#a8d5a2`, hover `#96c98f`, with dark ink; Delete run uses lighter red `#bb4c43` with white text. Error text and the outlined permanent-confirmation action keep darker red. [DESIGN.md](../../DESIGN.md) consolidates exact tokens and responsive rules; the [implementation handoff](implementation-handoff.md) defines production PRs and acceptance. Its 46px fields, 4px radius, heading line height 1.15 and readable disabled states take precedence over older specimen differences. Keep the approved 640px form cap. Allow action wrapping under enlarged text rather than shrinking targets or clipping labels.

## State-to-presentation matrix

| State | Accepted presentation and action |
| --- | --- |
| Create/edit ready, unchanged edit | Labeled fields, ordered section controls, separate notes, sticky actions; ordinary Save remains available when unchanged |
| Initial loading | Announced loading; fields hidden and writes disabled |
| Failed/unreadable initial load | Visible explanation, Retry, and return to schedule; no saveable empty editor |
| Initially missing run | Run unavailable and return action |
| Pending save/delete | Announced progress, busy semantics, competing edits/writes disabled; leaving does not cancel the request |
| Local/server validation, oversized request | Retained entries, inline errors and first-invalid-field focus; reduce notes/sections for oversized requests |
| Stale revision, reload required, uncertain edit save/delete | Retain readable draft, block writes, explain uncertainty where applicable, offer Reload saved run and return |
| Recovery reload failed/succeeded | Failed read retains draft and blocked writes with Retry reload; success loads current values for review without resubmission |
| Delete confirmation | Identify last loaded saved date/type, permanence and dirty-draft warning; Keep run focused first; editing/Save disabled |
| Keep run, rejected deletion | Keep draft and field feedback; Keep run returns focus to Delete run; a retry needs fresh explicit confirmation |
| Missing after write/reload | Retain draft for reference, disable writes, offer return without attributing deletion |
| Uncertain create/conflicting earlier create | Preserve existing same-run/unchanged-values retry guidance or submitted-week inspection, distinct from edit reload policy |
| Confirmed write, failed schedule refresh | Show read failure and Retry loading schedule without resending the write |

## Deletion and recovery contract

Delete run opens an inline confirmation above the footer. Identify the last loaded saved date and type, explain permanence, and warn that unsaved edits will be discarded when the form is dirty. Focus Keep run first. Opening or cancelling sends no write and preserves the draft and validation feedback. Keep run restores editing and returns focus to Delete run. Pending deletion focuses its progress message and disables competing actions. Never imply undo, skipping, or automatic saving of draft changes.

Keep the draft and baseline revision on stale or uncertain edit/delete results. Require an explicit saved-state reload before another write; do not adopt a revision, merge, or retry automatically. Reload warns before discarding changes. A failed reload retains the draft and blocked writes; a successful reload replaces values for review and requires a fresh save or deletion confirmation. Missing state does not identify which caller removed the run. Creation keeps its existing distinct retry/inspection behavior.

Cancel and Schedule navigation retain dirty-draft confirmation; leaving during a pending write explains that leaving does not cancel the request. Preserve accessible announcements, disabled/busy semantics, first-invalid-field focus, confirmation focus, drawer focus and Escape handling, and the existing save/cancel/delete return-week and fresh-read rules. A confirmed write followed by a failed schedule read retries only that read.

The [implemented browser contract](planned-run-editing-and-deletion.md#browser-flows-and-acceptance) remains authoritative for API, revision, validation, draft, and return-week behavior. Authentication/session-expiry remains in [its own decision](https://github.com/ArnaudJalbert/aweille/issues/39).

## Evidence and implementation checks

The [self-contained specimen](https://github.com/ArnaudJalbert/aweille/blob/a336dcbe2be9c2d08dd5f3c3cbcf2cc04848b9bd/docs/design/run-form-prototype.html) and [state matrix, 48 phone/desktop captures, run instructions, checks, and limits](https://github.com/ArnaudJalbert/aweille/blob/a336dcbe2be9c2d08dd5f3c3cbcf2cc04848b9bd/docs/design/run-form-review.md) are immutable primary sources on `chore/run-form-study`. Keep prototype code, fixtures, switches, and local save feedback off main.

The evidence records Chromium checks from 320px through 1280px, long-form sticky actions, exact large-target save/reopen, section controls/focus, validation/draft retention, saved-target deletion, explicit reload recovery, create retry distinctions, schedule-read retry without duplicate writes, and drawer behavior. This approval session rechecked confirmation focus, Keep run focus return, and uncertain-save blocked writes with retained draft. HTML renders at 390px and 1280px reported no console errors.

Implementation must preserve the existing public browser contracts in [creation](../../packages/aweille/tests/browser/test_run_creation.py), [editing/recovery](../../packages/aweille/tests/browser/test_run_editing.py), and [permanent deletion](../../packages/aweille/tests/browser/test_run_deletion.py), and verify presentation intentionally against the accepted matrix. The [integration record](../verification/redesign-acceptance.md) now verifies real HTTP/storage/concurrency recovery and actual desktop zoom. Physical-phone touch/software keyboards, hardware safe areas and screen-reader review remain pending. Specimen checks do not prove production behavior.
