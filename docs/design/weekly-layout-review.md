# Weekly layout review

Throwaway study for [Choose weekly layout and run-detail disclosure behavior](https://github.com/ArnaudJalbert/aweille/issues/44), October 17, 2026. The layout and interaction rules are proposals awaiting Arnaud's review. Production remains unchanged.

## Run

```sh
python3 -m http.server 8766 --bind 127.0.0.1 --directory docs/design
```

Open [weekly log](http://localhost:8766/weekly-layout-prototype.html?variant=log) or [selected day](http://localhost:8766/weekly-layout-prototype.html?variant=focus). The page is self-contained and also opens directly as a file. Plex fonts and their notices are copied from the [captured original study](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-ui-prototype.html).

The study compares the two existing compositions. Its controls select typical, busy, or empty fixtures; available or constrained content width; and loaded, loading, failed, or invalid-selection states. The floating arrows switch layouts. Left and right arrow keys also switch when focus is outside an interactive control.

Examples are illustrative layout data, not saved runs or training recommendations. The busy fixture includes 11 runs, timed and untimed siblings, a 14-section run, long notes, an unbroken reference, French text, and a 0.001 km section. Previous/next navigation changes the week; fixtures live in the week of October 12. This week uses the Montreal calendar date. Native browser back restores the selected week with details closed.

Run summaries use the existing edit paths as native links, intercepted in this study to open a modal side pane. The pane shows the clicked run's date, optional time, type, ordered section targets, and separate notes. Its Save preview changes only fixture memory. Add run opens the same pane in create mode, with the chosen day prefilled, optional time and notes blank, and required distance/pace targets blank. Add run to preview creates a local run and updates the schedule; the earlier navigation-simulation dialog has been removed. Reload or selecting another fixture clears local changes. The pane's geometry and complete form, deletion, and recovery states remain provisional for the later form-design decision.

## Proposal for review

Prefer the complete weekly log on phone and desktop. It exposes every day and every run summary together. The selected-day alternative gives details more width but hides the other days' summaries until selected. The narrow selected-day index wraps to preserve touch targets.

Retain the approved initially collapsed, independent disclosures. Summaries show run type, optional time or an explicit time-not-set label, exact total distance, section count, and a shared target pace or varied-pace label. Arnaud selected clicking the run to open its edit pane instead of a separate Edit button. The whole run summary is a native link, reachable with Tab and Enter. Hover and focus mark it as interactive. Show details remains a separate native disclosure, outside the link, so it never opens the editor or hides editing access behind expansion. Sections and labeled notes remain inside the disclosure.

Following Arnaud's next placement proposal, an empty day puts Add run in the content area instead of No runs planned. A day with one or more runs puts Add run below the day and date in the left column. There is exactly one date-scoped Add run per day. The compact orange button keeps its 28px visible height and click area at least 44px high and wide. On narrow screens the date column becomes the header above the runs, and the button follows the same content-dependent placement.

Keep opened disclosures and the selected day while opening and closing the pane. Close, Cancel, and Escape return focus to the clicked run. Dirty pane values prompt before discard. A preview save in the same week refreshes the schedule and keeps disclosures. A preview save into another week shows the saved date's week and resets disclosures. Both create and edit saves select the saved run's day in the selected-day composition and focus its summary so the result is visible. A week change and reload reset disclosures; no saved disclosure preference is implied. This replaces the earlier full-page-return proposal for edit cancellation.

Keep Add run scoped to its date. Create/save shows the saved date's week. Create cancellation closes the pane, returns focus to the original Add run, and leaves the originating week unchanged. For the selected-day alternative, arrival selects today in the current week or Monday in another week; opening and closing the pane does not change the selected day. Production create/edit/deletion destinations and current recovery behavior remain the baseline for the later integrated form design. The pane is an interaction specimen, not a finished replacement for those workflows.

Move week controls above the schedule. Loading and errors hide the old runs while keeping week controls available. Failure includes Retry, which restores the same selected week. An invalid selection disables previous/next and leaves This week available. Empty loaded weeks retain all seven Add run destinations.

The sidebar's design remains in its own decision. The 760px width option checks available space without implementing a sidebar or settling its threshold. The specimen keeps branding out of the page header, consistent with sidebar-only branding. Exact tokens and production font policy remain provisional.

## Evidence

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
