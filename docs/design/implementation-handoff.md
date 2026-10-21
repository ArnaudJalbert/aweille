# Running-app redesign implementation handoff

Arnaud approved the palette, type/geometry, three self-hosted font files, ordered production PRs, and acceptance requirements in [Finalize design tokens and implementation handoff](https://github.com/ArnaudJalbert/aweille/issues/47). This completes the design handoff for the [redesign planning map](https://github.com/ArnaudJalbert/aweille/issues/43). The production redesign and [Aweille redesign milestone](https://github.com/ArnaudJalbert/aweille/milestone/2) remain open until implementation and acceptance finish.

## October 18 visual precedence update

Current status on October 21: all three production PRs are merged. [Issue #51](https://github.com/ArnaudJalbert/aweille/issues/51) tracks the remaining focus follow-ups and manual acceptance. See the [updated integration evidence](../verification/redesign-acceptance.md#october-21-focus-follow-ups); earlier PR-preparation instructions below are historical. Keep the issue and milestone open until manual acceptance passes.

Arnaud subsequently requested the prototype's look directly in production. Use the [production visual reference](../../DESIGN.md#production-visual-reference), including paired phone date/target fields, full-width stacked notes, Sans field values and prototype control/state treatments. This supersedes earlier consolidated presentation differences below. Keep the production behavior, required checks, three open PRs and manual acceptance gates from this handoff.

October 21 phone follow-up: stack Planned date above optional Start time in phone/drawer mode below 900px of available application width. Desktop date/time and section distance/pace remain paired. Arnaud reported all requested physical iPhone Safari navigation, keyboard, rotation, safe-area, save/reopen and Keep run checks passed. Screen-reader testing is deferred at his request. See the [latest acceptance record](../verification/redesign-acceptance.md#october-21-phone-acceptance-and-date-fields).

## Unattended execution

When asked to implement the complete redesign while Arnaud is away, one agent owns [the foundation/sidebar](https://github.com/ArnaudJalbert/aweille/issues/29), [schedule](https://github.com/ArnaudJalbert/aweille/issues/50), and [forms/recovery](https://github.com/ArnaudJalbert/aweille/issues/51) in that order. The approved decisions and public browser/HTTP test seams are sufficient authorization for this scope. Settle reversible implementation details using the existing code and smallest working option; record the choice in the relevant PR instead of reopening design questions.

1. Read `AGENTS.md`, `CONTRIBUTING.md`, `PRODUCT.md`, `DESIGN.md`, the linked specification below and all three execution issues. Use `ponytail`. Claim the issues and inspect current branches/PRs before creating anything. Resume existing work rather than duplicate it.
2. Fetch origin and create an isolated feature worktree. Start from updated `origin/main` if it contains this handoff. If [the handoff PR](https://github.com/ArnaudJalbert/aweille/pull/52) is still open, use its fetched head as the documentation prerequisite and reference it in the implementation PRs. Preserve the main checkout's unrelated/untracked files. Run the setup commands in `CONTRIBUTING.md`; prototype branches are reference sources, not implementation starting points.
3. Implement and validate each layer before starting the next. Commit one focused branch per execution issue, run its required checks and open its PR targeting `main`. When a prerequisite PR is unmerged, start the next branch from its validated head and continue without waiting for Arnaud or a merge. Link every prerequisite PR and explain that the downstream diff temporarily includes those commits. Keep downstream PRs draft until their prerequisites merge. Native issue dependencies continue to describe review/merge order; they do not prevent this agent preparing dependent changes from the completed prerequisite code.
4. Run the full required checks at each layer and on the final combined head. Review and fix behavior, layout and accessibility failures. Capture representative phone/desktop/sidebar/form/recovery evidence using disposable test data. Preserve real public-page/API regression assertions, adapting only explicitly changed presentation/navigation expectations.
5. Leave implementation PRs open for review, with branch heads, dependencies, checks, evidence and outstanding manual checks recorded. Register all PRs with the thread when supported. Keep issue #51 and the redesign milestone open while final manual acceptance is pending; use `Refs: #51` rather than an automatic closing reference in that case. Publishing reviewable branches/PRs is authorized; this unattended brief does not request merging or deployment.

Implementation is ready for review when all three layers are committed/pushed, their PRs exist, the final combined head passes every required automated check, and the acceptance matrix distinguishes passed agent checks from pending human checks. Physical-phone, unavailable screen-reader and actual-device checks are a review checklist for Arnaud's return. Perform actual zoom or screen-reader checks if the environment supports them; report exactly what ran. Their unavailability must not stop implementation or PR preparation, and emulation must not be reported as physical-device evidence. A genuine external blocker should name the failed prerequisite, preserve finished work and allow independent work to continue.

Launch brief:

```text
Implement Aweille issues #29, #50 and #51 end to end in order. Follow
docs/design/implementation-handoff.md, including its unattended execution
section. If those docs are not on main yet, fetch PR #52 and use its head
as the documentation prerequisite. Complete all three layers without
waiting for my input or for prerequisite PRs to merge. Run the required
checks, prepare three PRs targeting main, and leave them open for review.
Record pending manual device/accessibility checks separately and keep
the final acceptance issue/milestone open. Do not merge or deploy.
```

## Specification and precedence

- [DESIGN.md](../../DESIGN.md) owns exact tokens, state treatments, type, geometry and responsive rules. It consolidates green Add run/Save, red Delete, readable disabled controls, and shared control sizes across the earlier studies.
- [Schedule composition](schedule-layout.md), [sidebar integration](sidebar-integration.md), and [form/deletion/recovery presentation](run-form-presentation.md) own approved interactions and the complete form-state matrix.
- [Production fonts](font-options.md#production-files) pins files, source commits, language coverage, notices and fallback behavior.
- [Implemented browser contracts](planned-run-editing-and-deletion.md#browser-flows-and-acceptance) remain authoritative for exact units, data/revisions, concurrency, validation, draft protection and recovery. Presentation and schedule navigation change only as explicitly selected above.

Immutable studies are evidence, not production code or automatic acceptance. Where specimen values differ, use the consolidated specification: 46px fields, 4px control radius, heading line height 1.15, green actions and readable disabled states.

## Minimal code boundaries

| Boundary | Responsibility |
| --- | --- |
| One base Jinja shell and sidebar include | Document metadata, font/CSS loading, skip link, sidebar/menu, screen content and page-specific module |
| One shared form-fields/section-template include | Persistent labels/units, date/time/type, ordered sections and separate notes; retain existing IDs and accessible associations |
| Existing `weekly.css` | One token/type/control layer plus named schedule, form and sidebar rules; no styling framework or component platform |
| Existing `run_form.js` | Exact conversion, section ordering/boundaries, validation associations and focus; reuse `createRunForm` |
| Separate `create_run.js` and `edit_run.js` | Existing write/reload/draft state ownership; creation and edit retry rules remain distinct |
| Small sidebar controller | Collapse/drawer state, resize, focus, inert background/scroll lock, dismissal, and guarded Schedule navigation |
| Schedule controller and small return-context helper | Day/Week/date/calendar, disclosures, URL/history, and one-use form return selection/focus |

Keep `/`, `/runs/new` and `/runs/{id}/edit`. Content-area placement does not require a single-page application. Share validated presentation context across these routes without moving API behavior into the shell. If a helper needs a separate module, name it for schedule navigation rather than inventing a generic UI framework. Do not merge the create/edit state machines or rewrite the API/core/storage.

Navigation context contains view, selected date/week, initiating control/run and the two views' manual disclosure choices. It carries no draft, payload or revision. A one-use, tab-scoped handoff may transport it across document navigation; consume it on the intended form return. Ordinary reload/history restoration reapplies disclosure defaults. Missing, invalid or unrelated context falls back safely to the URL and approved defaults. No durable disclosure/sidebar preference or draft persistence is introduced. Verify return behavior independently of browser back/forward caching.

Keep existing `week` links valid. Add explicit view/date selection without silently selecting a different week. Cancel/return keeps origin selection and focuses the initiating Add run/summary when present; otherwise focus the schedule heading. Confirmed create/edit selects the saved date and focuses that run. Cross-week saves reset disclosures; successful deletion uses the existing origin/baseline week rule and focuses the schedule heading. Direct form URLs retain their existing fallback return behavior. Submitted-week inspection links remain truthful for uncertain creation. The drawer calls the form's draft/pending-leave guard before Schedule navigation.

Preserve decimal strings and `BigInt` arithmetic for large exact targets. Summaries must compute total distance without `Number` rounding, retain the run type and section count, and label common or varied pace without implying a new training metric. Use native links and independent disclosures. Keep all sections and both note labels accessible after expansion.

## Form leave guards

The production baseline has edit dirty-Cancel/reload and browser-unload protection; `create_run.js` has no equivalent dirty/pending-leave guard. The approved form design requires protection in both modes. This is explicit frontend scope, not a promise that every required guard already exists.

In the foundation/sidebar layer, route Cancel and Schedule navigation through the current form controller and add the missing create guard. Create is clean when its raw field values and section order match the initial rendered form, including any prefilled date. Treat changed invalid/partial text as dirty too. Confirm explicit dirty departure and retain every field, error and section when declined. Use native `beforeunload` protection for dirty forms, subject to browser behavior. Native reload/close uses the browser's warning; do not promise custom text there.

During pending create/edit/delete, explicit departure asks whether to leave while the request may still complete. Declining keeps the form and request; accepting navigates without cancelling/aborting the server operation. After a confirmed successful write, navigate without obsolete discard warnings. Keep creation's UUID and same-values retry policy unchanged, and keep edit/delete revision and explicit-reload recovery unchanged. A small shared navigation helper is appropriate; draft and request state remain owned by their form controller. Verify clean/dirty/invalid drafts, declined/accepted Cancel and Schedule, pending departure and confirmed-write navigation at the existing public page/HTTP seam.

## Ordered production PRs

PRs must merge in order. The unattended agent may prepare subsequent branches and PRs from validated prerequisite heads before those merges, as described above. All belong to the Aweille redesign milestone. The first PR may ship the shared appearance around the current schedule; final Day/Week composition follows in the second PR. Its acceptance applies to the screen features available in that PR, then runs again with the completed design in the third. Do not represent an intermediate PR as completed redesign acceptance.

| Order | Execution issue | Scope | Checks |
| --- | --- | --- | --- |
| 1 | [Add responsive collapsible left navigation from variant A](https://github.com/ArnaudJalbert/aweille/issues/29) | Self-hosted fonts/notices, shared shell, exact CSS tokens/type/controls, sidebar across all three existing screens; keep write state ownership | Font load/fallback, contrast/focus, desktop/drawer geometry/dismissal, resize, all existing run behavior and guarded navigation |
| 2 | [Implement Day/Week schedule and navigation context](https://github.com/ArnaudJalbert/aweille/issues/50) | Day/Week, time column, exact summaries, calendar/Today, URL/history, disclosures and complete form return context | Empty/busy/multi-run content, exact numbers, calendar/keyboard/Montreal dates, disclosure independence/defaults, return selection/focus and real form round trips |
| 3 | [Apply the approved run-form and recovery presentation](https://github.com/ArnaudJalbert/aweille/issues/51) | Shared fields include, sticky actions and accepted loading/validation/deletion/recovery presentation; complete integration acceptance | Existing real HTTP write/recovery scenarios, long content, pending states, saved-target deletion, focus/drafts, final sidebar/schedule/form matrix and manual review |

Use affected browser tests and `ty` during work. Each production PR runs `uv run pytest`, `uv run ty check`, `uv run ruff check .`, and `uv run ruff format --check .` before completion. Write new behavior tests first at the existing public page/HTTP seams. Avoid private-state assertions and duplicate screenshot-only versions of behavioral tests.

## Intentional presentation-test changes

| Existing test assumption | Replacement | Preserve in that scenario |
| --- | --- | --- |
| [Weekly view](../../packages/aweille/tests/browser/test_weekly_view.py) always exposes seven days and all details | Explicit Day/Week selection; Day expanded/Week collapsed; expand disclosures before checking detail content | Exact large units, section order/repetition, chronological/untimed order, escaped plain text, note line breaks and no overflow |
| Weekly top brand and below-Sunday Previous/This/Next controls | Sidebar-only brand, approved menu/view/Today/calendar locations, plus the October 18 request for direct day/week arrows | Clear current selection, recovery, keyboard navigation and meaningful focus |
| Old schedule Tab sequence | Menu, view controls, Today, calendar, run summary and independent disclosure through native interactions | Visible focus, Enter/Space semantics and Retry-to-heading recovery |
| [Creation](../../packages/aweille/tests/browser/test_run_creation.py) hardcodes old green/red/white controls and two input columns at 320px | Stacked phone date/time, paired section targets and full-width note rows; compact footer targets | Add/remove/reorder focus, last-section rule, invalid feedback, visible errors, labels/units, targets and no overflow |
| JavaScript-unavailable page has no buttons anywhere | Truthful unavailable schedule/form state; no usable data/write actions; shell controls may exist without claiming loaded data | No invented empty schedule or saveable blank edit form |

Keep [creation contracts](../../packages/aweille/tests/browser/test_run_creation.py), [editing/recovery contracts](../../packages/aweille/tests/browser/test_run_editing.py), and [deletion contracts](../../packages/aweille/tests/browser/test_run_deletion.py). Adapt selectors and approved navigation assertions; do not remove the behavior they protect. Assert user-visible actions, saved state, network results and focus, not an implementation's helper calls.

## Acceptance matrix

| Area | Required evidence |
| --- | --- |
| Responsive geometry | All three screens at 320px, 390px, 900px and 1280px; 559/560px content boundary; 899/900px application boundary; constrained application inside a wider viewport; desktop expanded/collapsed; phone drawer closed/open |
| Narrow desktop content | Exactly 900px expanded application leaves 628px content; content-based rules still work with sidebar open; no page-wide horizontal overflow or clipped targets/notes |
| Schedule content | Empty Day, all seven empty Week dates, ordinary week, dense multi-run days, equal start times, untimed last, repeated sections, large exact values, long multiline/unbroken notes, absent notes |
| Disclosures and editing | Day initially expanded, Week collapsed; native Enter/Space/touch; independent Show/Hide actions with several open; summary edits the right run, disclosure never edits; per-view choices survive same-week switching and form cancel, reset on week change/reload/history |
| Calendar/navigation | Contextual day/week selection, month movement, arrow keys, Enter, shortcut, Cancel/Escape focus; direct day/week arrows with range limits and preserved focus; URL/reload/history selection; Today uses Montreal date when pressed, including midnight, DST and year boundaries |
| Form round trips | Date-scoped creation; cancel focus/selection retention; save/reschedule selects and focuses saved run; deletion returns to correct week/heading; direct form URL fallback; fresh schedule read and read-only Retry after confirmed writes |
| Sidebar | Full desktop collapse/reopen, closed initial drawer, close/backdrop/Escape/Schedule dismissal, focus containment/return, background inert/scroll lock, resize restoration, sidebar-only branding; drawer Escape precedes form behavior |
| Draft/pending behavior | Toggle preserves all fields; declined discard keeps draft; Schedule/Cancel/reload use guards; leaving does not cancel pending writes; no competing write or accidental resubmission |
| Form states | Every row of the [accepted state matrix](run-form-presentation.md#state-to-presentation-matrix), including unreadable/missing loads, unchanged save, local/server/oversize errors, stale/uncertain results, failed/successful reload and missing-after-write states |
| Deletion | Last loaded saved target despite changed draft, permanence/dirty warning, Keep run first focus and return, no write on opening/cancel, pending announcement, fresh explicit retry/confirmation, no implied undo/skip |
| Long form | Many ordered sections and long notes; sticky footer clearance, 320px ordinary single-row actions, enlarged-text reflow, usable short viewport/software keyboard and safe-area padding |
| Fonts/states | All three pinned files load from same origin; English/French samples; blocked fonts remain usable in Arial/monospace; no synthesized weights; real-content contrast, hover/active/focus, readable disabled/pending and distinct error/destructive states |
| Accessibility/manual | Full keyboard path and no focus obstruction, actual 200% zoom and reflow to 320 CSS px, enlarged text without lost actions, physical-phone touch/software keyboard/safe areas, and screen-reader naming/announcements/focus |

Browser-emulated widths and automated keyboard/HTTP checks may pass before manual acceptance. Record browser/device, version, checks, results and any fix in the final execution issue. Do not mark the redesign milestone complete until actual-phone, zoom and screen-reader reviews pass. Current specimens establish none of those manual results; production acceptance remains work to do. This gate does not block completing implementation, running automated checks, or opening all three PRs. Leave unavailable manual checks explicitly pending for Arnaud's return.

## Scope and remaining uncertainty

Retain Add run and existing date/time/type/section/note fields. Structure each run independently inside its day, with sections nested inside it, so future training blocks fit without a generic block API. Do not ship mixed-training fixtures, kind pickers, prototype switches, demo records, fake save feedback, charts, new storage/models, or a frontend migration.

Authentication/session expiry remains in [its own browser-flow decision](https://github.com/ArnaudJalbert/aweille/issues/39); deployment and final logo artwork remain separate. They do not block these implementation issues. No unresolved design choice blocks the sequence. Device rendering, font loading/fallback, production HTTP recovery integration and manual accessibility remain validation tasks, not assumed results.
