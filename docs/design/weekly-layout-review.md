# Weekly layout review

Throwaway study for [Choose weekly layout and run-detail disclosure behavior](https://github.com/ArnaudJalbert/aweille/issues/44), October 17, 2026. The layout and interaction rules are proposals awaiting Arnaud's review. Production remains unchanged.

## Run

```sh
python3 -m http.server 8766 --bind 127.0.0.1 --directory docs/design
```

Open [weekly log](http://localhost:8766/weekly-layout-prototype.html?variant=log) or [selected day](http://localhost:8766/weekly-layout-prototype.html?variant=focus). The page is self-contained and also opens directly as a file. Plex fonts and their notices are copied from the [captured original study](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-ui-prototype.html).

The study compares the two existing compositions. Its controls select typical, busy, or empty fixtures; available or constrained content width; and loaded, loading, failed, or invalid-selection states. The floating arrows switch layouts. Left and right arrow keys also switch when focus is outside an interactive control.

Examples are illustrative layout data, not saved runs or training recommendations. The busy fixture includes 11 runs, timed and untimed siblings, a 14-section run, long notes, an unbroken reference, French text, and a 0.001 km section. Previous/next navigation changes the week; fixtures live in the week of October 12. This week uses the Montreal calendar date. Native browser back restores the selected week with details closed.

The specimen uses the existing run paths as intercepted links. A separate review dialog simulates cancel, save, reschedule, and deletion return destinations, without presenting an editor design. All mutations affect memory only. Reload or selecting another fixture clears them.

## Proposal for review

Prefer the complete weekly log on phone and desktop. It exposes every day and every run summary together. The selected-day alternative gives details more width but hides the other days' summaries until selected. The narrow selected-day index wraps to preserve touch targets.

Retain the approved initially collapsed, independent disclosures. Summaries show run type, optional time or an explicit time-not-set label, exact total distance, section count, and a shared target pace or varied-pace label. Edit remains a sibling control outside the disclosure. Following Arnaud's feedback, Add run and Edit use compact orange buttons with dark labels, a 28px visible height, and a surrounding click area at least 44px high and wide. The earlier large outlined treatment is superseded. The smaller visible buttons keep the same destinations and focus behavior. The ordered sections and separately labeled notes appear inside it.

Keep opened disclosures while selecting days within one week. Reset on a week change, reload, and return from create/edit/delete, including cancel. Store no disclosure preferences. Native summary controls support Enter and Space with a visible 3px focus outline. A selected-day control keeps focus after activation. Week controls keep focus during navigation. Retry and simulated editor return focus the week heading.

Keep Add run scoped to its date. Preserve the current destinations: create/save returns to the saved date's week, cancel returns to the originating week, edit/save returns to the saved date's week, and deletion returns to the editor's originating week. These follow `create_run.js`, `edit_run.js`, and their browser tests. The selected-day alternative selects today in the current week or Monday in another week on arrival; it does not override those destinations to follow the edited run.

Move week controls above the schedule. Loading and errors hide the old runs while keeping week controls available. Failure includes Retry, which restores the same selected week. An invalid selection disables previous/next and leaves This week available. Empty loaded weeks retain all seven Add run destinations.

The sidebar's design remains in its own decision. The 760px width option checks available space without implementing a sidebar or settling its threshold. The specimen keeps branding out of the page header, consistent with sidebar-only branding. Exact tokens and production font policy remain provisional.

## Evidence

The compact-action revision was checked in both layouts at 320px, 390px, 760px, and 1280px. Visible buttons are 28px high with click areas at least 44px in both dimensions. Button text contrast is 4.92:1. Both actions still open their navigation previews, Escape restores focus, and keyboard focus remains visible. Expanded busy content fits without horizontal overflow. The screenshots below show this revision.

| Composition | Desktop | Phone |
| --- | --- | --- |
| Complete weekly log | [1280px viewport](weekly-layout-review/desktop-log.png) | [390px viewport](weekly-layout-review/phone-log.png) |
| Selected day | [1280px viewport](weekly-layout-review/desktop-focus.png) | [390px viewport](weekly-layout-review/phone-focus.png) |

Chromium checks passed for both layouts at 320px, 360px, 760px, and 1280px with expanded long content. There was no horizontal overflow, and visible specimen buttons, links, and summary targets were at least 44px high. The selected-day long-content check used Tuesday's 14-section example. A 640px viewport also checked reflow for the space available at 200% zoom from a 1280px viewport; this is a reflow check, not actual browser zoom or a physical-device check.

Interaction checks covered native Enter/Space disclosure, independent expansion, disclosure state across day selection, reset through week/history/editor return, rescheduling into another week, deletion, date-scoped creation, dialog Escape focus return, loading/error/invalid states, Retry focus, and an empty week with seven Add run actions. No browser errors or assertion failures occurred. Embedded self-checks cover exact fixture measurements, repeated sections, timed-first fixture order, and font loading.

The collaborative browser failed twice with `Preview automation snapshot timed out after 15000ms.` Checks and screenshots therefore used the project's installed Playwright Chromium. T3's separate HTML preview also rendered the study without console messages.

Read against `weekly.html`, `weekly.js`, `weekly.css`, `test_weekly_view.py`, the create/edit navigation code, and the create/edit/deletion browser tests. No production code or API was changed. The production test suite was not rerun for this isolated HTML study. Physical-phone rendering, screen-reader use, actual zoom, and integrated sidebar behavior remain unchecked.

Keep this prototype and its screenshots on `chore/weekly-layout-study`, outside main. Record the accepted decision after Arnaud's review, then update the durable design documents and resolve the ticket. This study alone does not approve the redesign or close the decision.
