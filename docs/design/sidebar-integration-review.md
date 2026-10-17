# Sidebar integration review

Disposable study for [Fit the approved sidebar into the new design](https://github.com/ArnaudJalbert/aweille/issues/45), October 17, 2026. Arnaud approved the sidebar integration, including the 224px width, 900px drawer threshold, menu placement, and interim branding. Complete form layout and recovery design remain separate decisions. Production is unchanged.

The question is where the already selected full sidebar, menu control, headings, and actions fit around the accepted schedule and provisional run pane. This retains variant A's navigation behavior rather than reopening the rejected icon rail and desktop overlay alternatives.

## Run

```sh
python3 -m http.server 8767 --bind 127.0.0.1 --directory docs/design
```

Open [the integration study](http://localhost:8767/sidebar-integration-prototype.html). The self-contained HTML also opens directly as a file. It embeds the approved schedule's Plex fonts and licence notices. Default fixture date is Wednesday, October 14, for review; it is illustrative data, not a training recommendation. Date labels remain relative to Montreal's actual current date.

Use the menu icon beside Week/Day, the sidebar collapse button, and the existing calendar, Today, Add run, and clickable runs. Screen and width selectors are study controls. Add/edit saves only change fixture memory. Reload resets the navigation and data.

## Approved sidebar integration

| Part | Selected behavior |
| --- | --- |
| Desktop sidebar | 224px, initially expanded, full collapse with no residual icon rail |
| Drawer threshold | Below 900px of available application width, not a user-agent check |
| Narrow desktop content | At 900px, an expanded sidebar leaves 628px after content padding |
| Phone drawer | Initially closed; up to 280px wide, leaving at least 44px of backdrop |
| Content | 24px desktop padding, 16px in drawer mode; schedule capped at 960px |
| Menu control | At the left of the schedule view switcher; beside the form heading in create/edit |
| Brand | Interim Aweille text in Plex Sans, only inside the sidebar, without a slogan |
| Navigation | Schedule is active; Run history and Trainer remain disabled placeholders |

Calendar and Add run stay beside their date heading. Today stays at the end of the schedule toolbar. The approved time column, Day default, expanded Day details, collapsed Week details, multiple runs, and absence of schedule arrows remain intact.

For integration review, the run pane occupies the content column and keeps navigation accessible rather than using the earlier modal overlay. Closing restores the schedule without rebuilding its disclosures. Final form geometry, section controls, deletion, and recovery presentations remain owned by [Define run-form, deletion, and recovery presentations](https://github.com/ArnaudJalbert/aweille/issues/46). This provisional placement does not settle that decision.

## Interaction rules

- Desktop collapse returns focus to the visible menu control and frees the sidebar column. The control remains available in schedule and form views.
- The phone drawer uses a native modal dialog, traps keyboard focus, and prevents background interaction and scrolling. Close, backdrop, and Escape dismiss it and return focus to its initiating menu control.
- Selecting Schedule closes a phone drawer and focuses the selected schedule heading. Leaving a changed run pane prompts before discard; declining retains the pane and its draft.
- Opening and closing navigation does not change dates, view, disclosures, or form values. Escape dismisses the drawer before it can dismiss a form behind it.
- Switching to a narrow layout closes the drawer. Returning to desktop restores the in-memory desktop collapse choice. Nothing persists across reload.

## Visual evidence

Desktop captures use 1280px; phone captures use 390px. Open phone drawers are captured within an 800px viewport. These are browser-rendered specimens.

| Screen | Desktop expanded | Desktop collapsed | Phone closed | Phone open |
| --- | --- | --- | --- | --- |
| Day | [View](sidebar-integration-review/desktop-expanded.png) | [View](sidebar-integration-review/desktop-collapsed.png) | [View](sidebar-integration-review/phone-closed.png) | [View](sidebar-integration-review/phone-open.png) |
| Week | [View](sidebar-integration-review/desktop-week.png) | [View](sidebar-integration-review/desktop-week-collapsed.png) | [View](sidebar-integration-review/phone-week-closed.png) | [View](sidebar-integration-review/phone-week-open.png) |
| Add run | [View](sidebar-integration-review/desktop-create.png) | [View](sidebar-integration-review/desktop-create-collapsed.png) | [View](sidebar-integration-review/phone-create.png) | [View](sidebar-integration-review/phone-create-open.png) |
| Edit run | [View](sidebar-integration-review/desktop-edit.png) | [View](sidebar-integration-review/desktop-edit-collapsed.png) | [View](sidebar-integration-review/phone-edit.png) | [View](sidebar-integration-review/phone-edit-open.png) |

## Verification and limits

T3 collaborative browser checks covered 320px, 390px, 760px, 900px, 1024px, and 1280px, plus an exactly 900px application container. Checks verified the responsive mode, desktop collapse/reopen, retained content, 44px menu controls, and no horizontal overflow. Drawer checks covered native modality, keyboard focus containment, close, Escape, backdrop, Schedule selection, focus return from the schedule and editor, and background scroll locking.

Form checks covered create/edit entry, date prefill, required blank creation targets, preserved values through menu toggles, draft keep/discard on Schedule navigation, Escape return, local creation with exact targets, saved-run focus, expanded Day details, and unavailable preview actions while loading failed. Week/calendar selection also remained usable beside the expanded sidebar. HTML previews for all sixteen captured states reported no console messages. Physical phones, screen readers, actual browser zoom, complete section editing/deletion/recovery, and production API integration remain unchecked. No application tests were rerun for this standalone specimen.

The approval refreshes the existing [sidebar execution issue](https://github.com/ArnaudJalbert/aweille/issues/29), including edit and deletion-flow coverage, the selected schedule rules, and the agreed threshold. No duplicate navigation implementation issue is needed. Form pane geometry remains provisional for the form decision.

## Sources

- [Accepted schedule study](https://github.com/ArnaudJalbert/aweille/blob/5d6e125fa8953d7844f5d70953af8b58d87f86ff/docs/design/weekly-layout-review.md)
- [Earlier selected sidebar and its original checks](https://github.com/ArnaudJalbert/aweille/blob/7ebee00998cda1e3b06e504a5e452cb41c044400/docs/design/navigation-prototype.md)
- [Durable schedule decision PR](https://github.com/ArnaudJalbert/aweille/pull/49)
- Current `weekly.html`, `create_run.html`, `edit_run.html`, editor draft guards, browser contracts, and [planned-run editing/deletion contracts](planned-run-editing-and-deletion.md)
