# Weekly layout review

Throwaway study for [Choose weekly layout and run-detail disclosure behavior](https://github.com/ArnaudJalbert/aweille/issues/44), October 17, 2026. The layout and interaction rules are proposals awaiting Arnaud's review. Production remains unchanged.

## Run

```sh
python3 -m http.server 8766 --bind 127.0.0.1 --directory docs/design
```

Open [weekly log](http://localhost:8766/weekly-layout-prototype.html?variant=log) or [selected day](http://localhost:8766/weekly-layout-prototype.html?variant=focus). The page is self-contained and also opens directly as a file. Plex fonts and their notices are copied from the [captured original study](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-ui-prototype.html).

The study compares the two existing compositions. Its controls select mixed, typical, busy, or empty fixtures; an activity grouping; available or constrained content width; and loaded, loading, failed, or invalid-selection states. The activity-layout selector retains the alternatives for reference. Week/Day switches the schedule view. The comparison-only floating toolbar was removed after the time column was selected; the only schedule arrows are now at the bottom and navigate dates.

Examples are illustrative layout data, not saved runs or training recommendations. The busy fixture includes 11 runs, timed and untimed siblings, a 14-section run, long notes, an unbroken reference, French text, and a 0.001 km section. Previous/next navigation changes the week; fixtures live in the week of October 12. This week uses the Montreal calendar date. Native browser back restores the selected week with details closed.

Run summaries use the existing edit paths as native links, intercepted in this study to open a modal side pane. The pane shows the clicked run's date, optional time, type, ordered section targets, and separate notes. Its Save preview changes only fixture memory. Add run opens the same pane in create mode, with the chosen day prefilled, optional time and notes blank, and required distance/pace targets blank. Add run to preview creates a local run and updates the schedule; the earlier navigation-simulation dialog has been removed. Reload or selecting another fixture clears local changes. The pane's geometry and complete form, deletion, and recovery states remain provisional for the later form-design decision.

## Activity layout comparison

Arnaud selected the time column after reviewing the three treatments. He preferred its compactness and clearer presentation of time. It is now the default activity layout; the other treatments remain available as references. This settles activity grouping. Arnaud subsequently requested a view switcher and a Today shortcut, retaining both the complete week and a single-day view.

Arnaud found several activities on one date hard to decode. The study now compares three treatments with identical examples and preserves the run-only fixtures. Mixed examples are the default for this comparison. They are future display specimens, with no non-running editor or API.

Wednesday contains stretching at 06:30, an interval run at 07:00, and untimed yoga. Friday adds a strength example. Durations, exercise counts, run distances, and paces retain their separate units. Several activities produce an explicit count beside the date. Timed activities remain chronological, followed by untimed ones. Each activity has its own kind, title, summary, and independent disclosure.

| Query | Treatment | What it tests |
| --- | --- | --- |
| `grouping=panels` | Separate panels | Full boundaries around each activity, a pale surface, explicit kind, and time in the corner. Retained comparison alternative. |
| `grouping=timeline` | Time column | Selected. A dedicated time column and fine vertical rule. Makes chronology prominent while staying compact; untimed items explicitly say Untimed. |
| `grouping=rows` | Compact rows | Strong horizontal rules with kind and time above the title and summary. The wide view aligns titles and measurements in columns. |

Use `fixture=mixed&variant=focus` and select Wednesday to compare one populated day, or use `variant=log` to inspect the weekly context. The activity-layout selector keeps content unchanged while switching treatments and preserves currently open details. The former floating treatment switcher is preserved in the earlier comparison commit. These earlier screenshots preserve the comparison state before the integrated Week/Day switcher.

| Activity treatment | Phone | Desktop |
| --- | --- | --- |
| Separate panels | [390px](weekly-layout-review/phone-activities-panels.png) | [1280px](weekly-layout-review/desktop-activities-panels.png) |
| Time column | [390px](weekly-layout-review/phone-activities-timeline.png) | [1280px](weekly-layout-review/desktop-activities-timeline.png) |
| Compact rows | [390px](weekly-layout-review/phone-activities-rows.png) | [1280px](weekly-layout-review/desktop-activities-rows.png) |

Chromium checks covered all three treatments in both weekly compositions at 320px, 390px, 760px, and 1280px. The 24 layout combinations retained correct order, counts, and units without horizontal overflow, including expanded notes. Keyboard disclosures remained independent and persisted across treatment changes. Run editing, local addition alongside non-running examples, fixture switching, and the floating layout switcher passed. No browser errors or embedded assertion failures occurred. Physical-phone and screen-reader checks remain outstanding.

## Proposal for review

Arnaud requested both views through an in-page Week/Day switcher, with Day as the default. Day shows only the selected date, with no week index. Week shows all seven days. Explicit view selections in the URL still take precedence. Today switches directly to Day on the current Montreal calendar date. A small calendar icon beside the heading opens a date picker. In Week view, choosing a date selects its whole Monday-to-Sunday week; the selected week is highlighted. In Day view, it selects only that day. Month arrows browse the picker, and its This Week/Today shortcut returns to the current interval without changing views. Calendar dates support arrow-key movement and Enter selection; Cancel or Escape returns focus to the calendar icon. Simple icon arrows above and below the schedule move by one week or day, with contextual accessible names and hover labels. The two navigation landmarks have distinct top/bottom labels.

The primary heading is relative to Montreal's current calendar date. Week titles are This Week, Next Week, In 2 Weeks, Last Week, or N Weeks Ago. Day titles use Today, Tomorrow, Yesterday, In N Days, or N Days Ago. Exact dates remain visible below the heading. Week differences use Monday-based calendar arithmetic, including across daylight-saving and year boundaries. The user's requested title casing applies to these headings.

Arnaud requested expanded details by default in Day view. Week keeps its initially collapsed details. Each view remembers its own manual toggles until a week change or reload, so collapsing a Day activity does not change its Week disclosure. Summaries show run type, optional time or an explicit time-not-set label, exact total distance, section count, and a shared target pace or varied-pace label. Arnaud selected clicking the run to open its edit pane instead of a separate Edit button. The whole run summary is a native link, reachable with Tab and Enter. Hover and focus mark it as interactive. Show/Hide details remains a separate native disclosure, outside the link, so it never opens the editor or hides editing access behind expansion. Sections and labeled notes remain inside the disclosure.

Following Arnaud's next placement proposal, an empty day puts Add run in the content area instead of No runs planned. A day with one or more runs puts Add run below the day and date in the left column. There is exactly one date-scoped Add run per day. The compact orange button keeps its 28px visible height and click area at least 44px high and wide. On phone widths, Add run instead sits to the right of the day/date heading on every day, whether empty or populated. This uses the spare header space and keeps the button in place when the first run is added. The desktop content-dependent placement remains unchanged.

Keep opened disclosures and the selected day while opening and closing the pane. Close, Cancel, and Escape return focus to the clicked run. Dirty pane values prompt before discard. A preview save in the same week refreshes the schedule and keeps disclosures. A preview save into another week shows the saved date's week and resets disclosures. Both create and edit saves select the saved run's day in the selected-day composition and focus its summary so the result is visible. A week change and reload reset disclosures; no saved disclosure preference is implied. This replaces the earlier full-page-return proposal for edit cancellation.

Keep Add run scoped to its date. Create/save shows the saved date's week. Create cancellation closes the pane, returns focus to the original Add run, and leaves the originating week unchanged. Switching between Week and Day keeps the selected date and restores that view's disclosure choices. Newly added activities follow the selected view's default. Without a date in the URL, Day starts on today within the current week or Monday in another week. The URL records both view and date; reload and browser Back/Forward restore them. Today resolves the date when pressed, including after midnight, independent of the browser's timezone. Opening and closing the pane does not change that selection. Production create/edit/deletion destinations and current recovery behavior remain the baseline for the later integrated form design. The pane is an interaction specimen, not a finished replacement for those workflows.

The calendar icon stays near the heading and the previous/next arrows sit above and below the schedule. Loading and errors hide the old activities while keeping date controls available. Failure includes Retry, which restores the same selected week. An invalid selection disables previous/next and leaves This week available. Empty loaded weeks retain all seven Add run destinations.

The sidebar's design remains in its own decision. The 760px width option checks available space without implementing a sidebar or settling its threshold. The specimen keeps branding out of the page header, consistent with sidebar-only branding. Exact tokens and production font policy remain provisional.

## Evidence

Top and bottom navigation passed at 320px, 390px, and 1280px. Both sets use the selected view's day/week interval, support keyboard activation, and disable on an invalid selection. Placement and horizontal overflow checks passed with no browser errors. Examples are [phone](weekly-layout-review/phone-top-navigation.png) and [desktop](weekly-layout-review/desktop-top-navigation.png).

Default-view checks passed for a fresh URL, invalid view value, explicit Day and Week links, reload after choosing Week, and history restoration without a view parameter. Day opens with its activity details expanded. No browser errors occurred.

The Day-default revision passed at 320px and 1280px. Checks covered expanded Day versus collapsed Week defaults, independent manual choices across view switches and Today, keyboard toggling, treatment changes, editor cancellation, new-run expansion, reload and week resets, and horizontal overflow. No browser errors occurred. Expanded Day examples are [phone](weekly-layout-review/phone-day-expanded.png) and [desktop](weekly-layout-review/desktop-day-expanded.png).

The calendar and relative-heading revision passed at 320px, 390px, 760px, and 1280px. Checks covered whole-week versus single-day selection, seven versus one highlighted dates, month navigation, arrow-key date focus and Enter selection, Cancel/Escape focus return, relative labels for past/current/future intervals, bottom-arrow placement, date-scoped creation, history and reload, Montreal versus Tokyo dates, and daylight-saving/year boundaries. No browser errors occurred. The calendar examples are [phone](weekly-layout-review/phone-date-picker.png) and [desktop](weekly-layout-review/desktop-date-picker.png).

| Relative heading and bottom arrows | Phone | Desktop |
| --- | --- | --- |
| Week | [390px](weekly-layout-review/phone-relative-log.png) | [1280px](weekly-layout-review/desktop-relative-log.png) |
| Day | [390px](weekly-layout-review/phone-relative-focus.png) | [1280px](weekly-layout-review/desktop-relative-focus.png) |

The following switcher screenshots preserve the preceding navigation treatment.


The integrated switcher passed checks at 320px, 390px, 760px, and 1280px for seven-day versus one-day rendering, disclosure preservation across view changes, date-scoped Add run, empty days, day navigation across a week boundary, reload, browser Back, edit rescheduling, and invalid-selection recovery. A browser set to Tokyo with a controlled UTC clock verified Today against Montreal both before and after Montreal midnight. No browser errors occurred. The checks do not establish physical-phone or screen-reader compatibility.

| Current view | Phone | Desktop |
| --- | --- | --- |
| Week | [390px](weekly-layout-review/phone-switcher-log.png) | [1280px](weekly-layout-review/desktop-switcher-log.png) |
| Day | [390px](weekly-layout-review/phone-switcher-focus.png) | [1280px](weekly-layout-review/desktop-switcher-focus.png) |


The phone placement was checked in both compositions at 320px and 390px with empty and populated days. Add run sits to the right of the day/date heading, remains in that position after creating the first run, and keeps its selected-date prefill. No horizontal overflow occurred. The phone screenshots show this revision.

The create interaction passed in both layouts at 320px and 1280px. Checks covered chosen-date prefill, required blank targets preventing empty submission, exact sample measurements, an empty day becoming populated and moving its Add run button, a second run with timed-first ordering, cancel returning focus without creating a run, editing the newly added run, a changed save date selecting the correct day/week, and reload clearing local additions. No browser errors occurred. [Desktop create pane](weekly-layout-review/desktop-create-pane.png), [phone create pane](weekly-layout-review/phone-create-pane.png), and [schedule after adding a run](weekly-layout-review/after-add-run.png) capture the interaction.

The conditional Add run placement was checked against empty, typical, and busy fixtures in both layouts at 320px and 1280px. Each visible day has exactly one Add run, located in the content area when empty or below its date when populated. Date-scoped activation and narrow-layout fit passed.

The clickable-run revision was checked in both layouts at 320px, 390px, 760px, and 1280px. Click and Enter open the clicked run in the pane. Enter/Space on Show details expand only that run without opening the pane. Edit cancellation returns focus to the run and preserves disclosures. Preview edits, exact sample distance/pace values, rescheduling, and dirty-close keep/discard choices passed. The pane and expanded busy content fit without horizontal overflow; no browser errors occurred. The current screenshots also include the revised Add run placement.

[Desktop edit pane](weekly-layout-review/desktop-editor-pane.png) and [phone edit pane](weekly-layout-review/phone-editor-pane.png) show the interaction specimen. Full production state coverage remains part of the later form decision.

Add run retains its 28px visible button, a click area at least 44px high and wide, and 4.92:1 text contrast.

| Composition | Desktop | Phone |
| --- | --- | --- |
| Complete weekly log | [1280px viewport](weekly-layout-review/desktop-log.png) | [390px viewport](weekly-layout-review/phone-log.png) |
| Selected day | [1280px viewport](weekly-layout-review/desktop-focus.png) | [390px viewport](weekly-layout-review/phone-focus.png) |

Chromium checks passed for both layouts at 320px, 360px, 760px, and 1280px with expanded long content. There was no horizontal overflow, and visible specimen buttons, links, and summary targets were at least 44px high. The selected-day long-content check used Tuesday's 14-section example. A 640px viewport also checked reflow for the space available at 200% zoom from a 1280px viewport; this is a reflow check, not actual browser zoom or a physical-device check.

Interaction checks covered native Enter/Space disclosure, independent expansion, disclosure state across day selection, reset through week/history/editor return, rescheduling into another week, deletion, date-scoped creation, dialog Escape focus return, loading/error/invalid states, Retry focus, and an empty week with seven Add run actions. No browser errors or assertion failures occurred. Embedded self-checks cover exact fixture measurements, repeated sections, timed-first fixture order, and font loading.

The collaborative browser failed twice with `Preview automation snapshot timed out after 15000ms.` Checks and screenshots therefore used the project's installed Playwright Chromium. T3's separate HTML preview also rendered the study without console messages.

Read against `weekly.html`, `weekly.js`, `weekly.css`, `test_weekly_view.py`, the create/edit navigation code, and the create/edit/deletion browser tests. No production code or API was changed. The production test suite was not rerun for this isolated HTML study. Physical-phone rendering, screen-reader use, actual zoom, and integrated sidebar behavior remain unchecked.

Keep this prototype and its screenshots on `chore/weekly-layout-study`, outside main. Record the accepted decision after Arnaud's review, then update the durable design documents and resolve the ticket. This study alone does not approve the redesign or close the decision.
