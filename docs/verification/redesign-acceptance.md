# Running-app redesign acceptance

Implementation for #29, #50 and #51 follows the merged #52 handoff. The implementation PRs remain open in dependency order; the two downstream PRs remain draft while their prerequisites are unmerged. This record describes the implementation branches and their disposable local verification, not a deployed application. Physical-phone and screen-reader acceptance remain pending, so #51 and the Aweille redesign milestone stay open.

```text
#53 foundation/sidebar -> #54 Day/Week/context -> forms/recovery PR
  -> automated/public-browser checks and actual desktop zoom
  -> maintainer review, physical phone and screen reader
  -> milestone completion only after acceptance
```

## Environment and checks

Verification ran on macOS with Playwright Chromium 156.0.8078.4, Uvicorn and temporary file-backed SQLite. Browser tests use real page/HTTP interfaces; write-failure tests either retain the real committed response or inject failures at HTTP. No real training database, API/core/storage code, deployment configuration or runtime dependency changed.

The final combined implementation head `551dfd4` passes all 366 tests in 82.15 seconds, `uv run ty check`, `uv run ruff check .`, `uv run ruff format --check .`, and `git diff --check`. The foundation and schedule layers also passed their complete required checks before the next branch was built, with 350 and 356 tests respectively. See their [foundation](redesign-foundation.md) and [schedule](redesign-schedule.md) records for intermediate evidence. Final review corrections were also applied to the schedule prerequisite and revalidated before restacking the form branch.

The additional integration pass exercised 16 combinations of Day, Week, create and edit at 320, 390, 900 and 1280 CSS px, using dense equal-time and untimed runs, twelve repeated sections, exact large targets, French text and long unbroken notes. It checked expanded/collapsed desktop navigation, closed/open drawers, backdrop/close/Escape dismissal, focus return, inert background, scroll lock, retained invalid/dirty drafts and page overflow. All passed. The appearance pass sent no write to storage.

## Integrated acceptance matrix

| Area | Result and evidence |
| --- | --- |
| Responsive geometry | Passed public browser checks at 320/390/899/900/1280px and 559/560px content thresholds. Constrained application width controls navigation independently of the wider viewport. Exactly 900px expanded leaves 628px content; desktop collapse frees 224px. Forms cap at 640px and schedule at 960px. |
| Schedule content | Empty Day, all seven Week destinations, dense/equal-time runs, untimed last, repeated sections, huge exact values, long/plain-text notes and absent notes passed. Summaries use BigInt, including the asserted `9007199254740994.123 km` case. |
| Disclosures/editing | Day open and Week closed defaults, native keyboard controls, independent choices, per-view/same-week retention, form Cancel, week changes and reload/history defaults passed. The summary edits the correct run independently of disclosure. |
| Calendar/navigation | Contextual day/week highlight, month movement, arrow keys/Enter, shortcut, Cancel/Escape focus, URL/history, invalid/boundary dates and Montreal midnight in a Tokyo browser passed. UTC calendar arithmetic handles week/year/DST boundaries; Today resolves when pressed. No schedule arrows remain. |
| Return context | Real create/edit/delete and Cancel round trips passed. Saved dates select the destination and focus the run. Cross-week moves reset disclosures. Missing/consumed context preserves origin/baseline fallback and focuses the heading, including after a form reload. Context transports no draft, payload or revision. |
| Sidebar | All three routes passed the integration width/state pass. Drawer focus containment, inert background, scroll lock, close/backdrop/Escape return and desktop resize restoration passed. A declined form departure preserves draft and validation. Branding appears only in navigation. |
| Dirty/pending behavior | Raw invalid create drafts and dirty edit drafts retain fields/errors after declined Cancel/Schedule/unload. Pending create/edit/delete prevent competing writes and explain that leaving does not cancel the request. Clean pending edit is protected too. Confirmed-write navigation avoids obsolete discard warnings. |
| Sections/units | Add/remove/reorder focus, boundary controls, last-section protection, optional time and notes, exact conversions and huge/repeated targets passed existing real-write scenarios. |
| Long forms/footer | Many sections and long notes passed with sticky footer clearance at ordinary heights, one-row 320px actions, 44px targets and enlarged-action wrapping. At viewport heights up to 480px the footer joins document flow so a short viewport can reach fields and actions. Bottom padding includes the hardware safe-area environment value. Physical software-keyboard/safe-area operation remains pending. |
| Fonts/states | Three same-origin WOFF2 files match pinned SHA-256, exact 400/500/400 weights and full notices. English/French and blocked-font fallback passed on all routes. Synthesis is disabled; emphasis is 500. Hover/active, destructive, blue focus, readable disabled/pending and error states passed. Forced-color selected dates retain a distinct 3px focus outline. |
| Contrast | Rendered control colors produced ink/green 8.84:1, disabled ink/panel 6.07:1, error/panel 7.00:1, white/Delete 4.97:1, control boundary/panel 3.88:1 and focus/paper 5.87:1. Text pairs pass 4.5:1 and boundary/focus pairs pass 3:1. |
| JavaScript unavailable | Restored the real navigation/module-blocking regression. The page explains why data cannot load and does not invent an empty schedule or usable write form. If a form module fails, shared Schedule navigation remains operable. |
| Desktop zoom/keyboard | Actual Firefox 158.0 at 200% zoom was exercised through native browser controls on schedule, create and edit. The browser showed its 200% indicator; navigation reflowed to drawer mode and labels/fields/footer actions remained readable and operable. Zoom was restored and the temporary tab closed. Automated keyboard paths cover calendar, disclosures, fields, section controls, confirmation, navigation and recovery with visible focus. |
| Remaining manual acceptance | Physical-phone touch/software keyboard/hardware safe areas, screen-reader names/announcements/focus, and maintainer review of 320 CSS px reflow/enlarged text remain pending. Automated width/text enlargement and native desktop zoom are recorded separately and do not substitute for these checks. |

## Form-state matrix

| Accepted state | Verified behavior |
| --- | --- |
| Ready/unchanged | Shared persistent labels/units and ordinary Save. Real unchanged PATCH remains `{}` and retains its revision. |
| Initial loading | Fields and Delete hidden, writes disabled, loading announced and form busy. |
| Failed/unreadable initial read | Explanation and Retry; no enabled blank editor. Invalid UUID/missing read cannot become creation. |
| Initially missing | Unavailable explanation and return; no enabled write or fabricated run. |
| Pending save/delete | Draft retained, inputs/competing writes disabled, busy/progress announced; deletion progress receives focus. |
| Local/server/oversized validation | Entered values and separate notes retained; associated field errors and first-invalid focus. Oversized edits explain reducing notes/sections and permit correction. |
| Stale/reload-required/uncertain edit/delete | Readable draft remains, Save/Delete blocked, explicit saved-state reload. Tests include missing/malformed preconditions and committed network/503/unreadable responses. |
| Failed/successful reload | Failed GET preserves draft and blocked state. Success replaces baseline/current fields for review, clears old errors, and requires a fresh explicit write. |
| Delete confirmation | Inline saved date/type despite changed draft; permanent-removal and draft-loss warning; Keep run first focus; opening/cancelling sends no write. |
| Keep run/rejected deletion | Draft and validation remain; focus returns to Delete. Rejection closes confirmation so retry requires a fresh explicit choice. |
| Missing after write/reload | Draft remains for reference and writes stay blocked. The notice does not attribute who removed the run or imply undo. |
| Uncertain/conflicting create | Same UUID/unchanged-values retry and submitted-week inspection remain distinct from edit reload policy. Inspection explicitly opens Week. |
| Confirmed write/failed schedule read | Old cards stay hidden; Retry only reads the schedule. The real cross-week creation test counts one POST and focuses the saved run after recovery. |

## Screenshots and review

All screenshots use disposable records, not training data. The existing design studies remain historical references.

- [Create desktop](redesign/form-create-desktop.png), [create phone](redesign/form-create-phone.png), [edit desktop](redesign/form-edit-desktop.png), [edit phone](redesign/form-edit-phone.png)
- [Initial loading](redesign/form-initial-loading-phone.png), [initial read failure](redesign/form-initial-failure-phone.png)
- [Saved-target deletion confirmation](redesign/form-delete-confirmation-phone.png), [pending deletion](redesign/form-pending-delete-phone.png), [uncertain save](redesign/form-uncertain-save-phone.png)
- Day/Week/calendar phone and desktop evidence is linked from the [schedule record](redesign-schedule.md).

The code-review skill ran independent Standards and Spec reviews against the merged handoff baseline. Findings were corrected and both axes reviewed again at `551dfd4`. No finding was dismissed as manual acceptance.

### Standards

No remaining documented-standard violations or actionable smells. The second pass confirmed fixes for the weakened JavaScript-unavailable test, forced-color focus, 12px time labels and duplicate CSS declarations. The reviewer checked the usefulness of the new return, DST, calendar and disclosure assertions and the accuracy of the acceptance record. This axis did not independently repeat the full suite or manual browser evidence.

### Spec

No remaining specification findings. The direct/missing-context return now preserves the fallback destination and focuses the schedule heading, including after a failed schedule read and retry. The second pass confirmed the fix and passed 40 focused public-browser navigation/edit/delete regressions. Physical-phone and screen-reader acceptance remain pending.

Review totals: Standards 0 remaining findings; Spec 0 remaining findings.

No implementation PR has been merged and nothing has been deployed. #52 was merged only after Arnaud explicitly approved it. Authentication/session expiry, future training kinds and custom logo work remain outside these changes.
