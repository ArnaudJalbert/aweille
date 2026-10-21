# Day/Week schedule verification

## Visual review correction

The October 18 review identified presentation omitted from the [approved sidebar/schedule specimen](https://github.com/ArnaudJalbert/aweille/blob/76e8ade669d2932542a336eeabd9e06cc63213f1/docs/design/sidebar-integration-review.md). Corrected captures below now show the Training schedule label, Week/Day order, right-aligned line-icon calendar, 116px desktop day column, time-column timeline and markers, Running labels, run counts, plus/minus disclosures and flat section/note treatment. Phone dates sit below weekdays. Day no longer repeats its selected date as a second heading. The contextual calendar again names the chosen day/week and uses the specimen's compact geometry.

The captures use representative run-only disposable data, so the approved study's future stretching/yoga/strength examples are intentionally absent. Green actions, 13px buttons, readable disabled controls, 14px time labels and 4px radii retain the consolidated handoff values where older captures differ. Public browser regressions now check the missing hierarchy, timeline and desktop collapse/focus as well as existing behavior.

Layer 2 for [#50](https://github.com/ArnaudJalbert/aweille/issues/50), built from the validated [foundation PR #53](https://github.com/ArnaudJalbert/aweille/pull/53). Review and merge #53 first. This branch deliberately includes its commits while it remains unmerged.

```text
URL view/date + Montreal calendar
  -> selected Day or seven-date Week
  -> exact summaries + native independent details
  -> one-use form handoff
     -> Cancel: origin selection, disclosures and initiating focus
     -> save: saved date/run focus, fresh read
     -> deletion: origin/baseline week and heading
```

Schedule state stays in the schedule controller. Calendar keyboard/month interaction has a small separate controller. `schedule_navigation.js` shares date validation and the single-use tab context across existing routes. A context is validated against the intended form path/query, consumed into page memory, then returned through a token tied to the destination selection. It contains no drafts, payloads or revisions. Reload/history restore URL selection with disclosure defaults. Storage being unavailable falls back to ordinary local URLs.

A confirmed write returns to a fresh API read. If it fails, Retry performs only that read and still focuses the saved run once it loads. Creation's submitted-week inspection links explicitly use Week, so the earlier write remains inspectable independently of the Day default.

Public browser/HTTP scenarios protect exact large values and section order, safe text/line breaks, independent Day/Week disclosure choices, same-week date changes and form Cancel, default reset on reload, real create/edit/delete round trips, recovery/concurrency, read-only Retry, URL/history, invalid and boundary dates, calendar arrows/Enter/Escape/month movement and selected-week highlighting. Montreal Today is resolved when pressed across midnight in a Tokyo browser and across the year boundary. Calendar arithmetic uses UTC dates rather than elapsed local DST hours.

The existing presentation/navigation assertions now use explicit Week selection and expand disclosures before checking details; behavior and saved-state assertions remain. New summary checks protect `9007199254740994.123 km` and varied pace without converting decimal strings to Number.

Screenshots use Playwright Chromium 156.0.8078.4 on macOS, October 17, 2026, with disposable API-created records in a temporary database:

- [Day desktop](redesign/schedule-day-desktop.png) and [390px Day](redesign/schedule-day-phone.png)
- [Week desktop](redesign/schedule-week-desktop.png) and [390px Week](redesign/schedule-week-phone.png)
- [Contextual calendar on phone](redesign/schedule-calendar-phone.png)

The T3 preview initially worked, then twice failed its snapshot operation with `Preview automation snapshot timed out after 15000ms.` Captures therefore use the repository's documented Playwright browser workflow.

Physical-phone, actual zoom, screen-reader and complete form presentation acceptance remain pending for the final integrated layer. Browser widths are emulation, not physical-device evidence. No merge or deployment is requested.

Required checks passed on this layer: `uv run pytest` with 355 tests; `uv run ty check`; `uv run ruff check .`; `uv run ruff format --check .`; and `git diff --check`.

The final integrated review also corrected this prerequisite: measurement times use 14px, forced-color selection no longer overrides focus, and missing/consumed form context returns heading focus while preserving its fallback week. Restored the JavaScript-disabled/missing-module scenario's real navigation and explanatory-status assertions. A new public form-reload regression protects one-use context. The updated schedule head passed all 356 tests and every required static/diff check before the form branch was restacked.
