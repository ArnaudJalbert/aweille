# Schedule composition and interactions

Accepted by Arnaud on October 17, 2026 through [Choose weekly layout and run-detail disclosure behavior](https://github.com/ArnaudJalbert/aweille/issues/44). This records the selected design implemented by the browser schedule. See [schedule verification](../verification/redesign-schedule.md) and [integrated acceptance](../verification/redesign-acceptance.md) for the implementation PRs and remaining manual checks.

## Views and activities

- Day is the default on phone and desktop. It shows only the selected date, without a week index. Week shows all seven days, including empty days. A Week/Day switcher stays inside the product header.
- Use the compact time-column treatment. Each independent activity shows its time or Untimed, kind/name, and relevant summary. Timed activities come first chronologically, followed by untimed activities. Preserve several runs on one date and stable ordering for equal times.
- Run summaries show run type, exact total distance, section count, and shared pace or varied pace. Sections retain their order; personal and trainer notes remain separate.
- Mixed stretching, strength, and yoga examples establish room for future independent blocks. They do not authorize new production activity kinds, editors, metrics, or API changes. Production retains Add run and existing run fields.

## Date selection

The small calendar icon near the heading opens a date picker. In Day, choosing a date selects that day. In Week, choosing any date selects its Monday-to-Sunday week and highlights all seven dates. The picker supports month navigation, arrow-key focus movement, Enter selection, and a contextual Today/This Week shortcut. Cancel or Escape returns focus to the calendar icon. There are no previous/next arrows above or below the schedule.

The main Today shortcut switches to Day on Montreal's current calendar date. Resolve the date when pressed, including after midnight and when the browser uses another timezone. Preserve the selected date when switching views. Without an explicit date, select today within the current week or Monday within another selected week.

Relative headings use This Week, Next Week, In 2 Weeks, Last Week, or N Weeks Ago. Day uses Today, Tomorrow, Yesterday, In N Days, or N Days Ago. Keep the exact date or date range visible underneath. Week differences use Monday-based calendar arithmetic across daylight-saving and year boundaries. These selected relative titles are an exception to the general sentence-case rule.

Record the selected view and date in the URL. Explicit view selection takes precedence over the Day default. Reload and browser history restore that selection, with disclosure defaults reapplied.

## Details and run actions

Day starts with every activity's details expanded. Week starts collapsed. Disclosures are independent native controls, usable with Enter, Space, or touch, with accessible naming and visible Show/Hide details text. Several may stay open. Each view keeps its own manual choices while changing dates within the same week, switching views, or opening and closing the pane. A week change or reload resets to the selected view's default. No saved disclosure preference is implied.

Click or tap the run summary to open its edit pane. Use a native link reachable with Tab and Enter, with visible hover/focus feedback. There is no separate Edit button. The detail disclosure remains outside this link and never opens editing. Closing or cancelling the pane returns focus to the initiating run and preserves schedule selection and disclosure choices. Dirty drafts require protection before discard.

Add run is compact and green with a 28px visible button and at least a 44px click area. The [consolidated tokens](../../DESIGN.md) supersede the historical orange captures. In Week on desktop, it replaces the empty-day placeholder or sits beneath the weekday/date for a populated day. On phones, it sits to the right of each day/date heading and stays there after the first run is added. In Day, it sits beside the selected-date heading. There is one date-scoped Add run for each visible day.

Add run opens the shared pane with the date prefilled and required targets blank. Cancel returns focus without changing the schedule. A successful create/edit save selects the saved run's date and focuses its summary; rescheduling across weeks shows the destination week and resets disclosure choices. New runs follow the selected view's disclosure default. Complete pane geometry, section controls, deletion, server validation, and recovery presentation belong to [the form decision](https://github.com/ArnaudJalbert/aweille/issues/46), preserving the existing behavior contracts.

## States, evidence, and remaining checks

Loading and failures hide old activities while keeping date selection available. Failure offers Retry for the same selection. Invalid selection keeps calendar and Today recovery available. Empty Week retains seven Add run destinations; empty Day retains its selected date and Add run action.

The [accepted study and evidence](https://github.com/ArnaudJalbert/aweille/blob/5d6e125fa8953d7844f5d70953af8b58d87f86ff/docs/design/weekly-layout-review.md) retain the self-contained interactive prototype and final phone/desktop Day/Week captures on a disposable branch. Earlier screenshots preserve superseded iterations. Browser checks cover narrow and desktop widths, exact sample units, independent disclosures, keyboard actions, create/edit preview return, date selection/history, Montreal dates, long content, empty/busy weeks, and absence of schedule arrows.

The [sidebar integration](sidebar-integration.md) is also approved. [DESIGN.md](../../DESIGN.md) and the [implementation handoff](implementation-handoff.md) settle exact tokens, fonts and the production sequence. The [integration record](../verification/redesign-acceptance.md) now covers real browser/API/sidebar/recovery checks and actual Firefox 200% zoom. Physical-phone and screen-reader acceptance remain pending. The prototype's local save feedback and fixtures must stay out of production.
