# Prototype presentation in production

Arnaud asked on October 18 to use the approved prototype's look directly in production. The final green [form specimen](https://github.com/ArnaudJalbert/aweille/blob/a336dcbe2be9c2d08dd5f3c3cbcf2cc04848b9bd/docs/design/run-form-prototype.html) is now the visual reference for the current run screens. The first implementation and its first correction still changed the phone form and control treatments. This final presentation pass removes those differences.

## Ported presentation

Date/time and distance/pace remain paired at phone widths. Notes use full-width vertical rows under Notes. Editable values use Plex Sans. Form headings, label units, quiet section actions, arrow controls, footer padding and green/red button borders follow the specimen. Schedule toolbar buttons use its 16px regular text; Add run and form actions use 13px medium text. The tinted navigation selection has the prototype's green edge and disabled navigation/action appearance. Draft values and progress remain opaque and readable. Recovery controls now sit inside the same notice panel as their explanation. The calendar keeps its contextual title, native keyboard semantics and visible Today marker.

The real create/edit/delete controllers, UUID/revision policies, exact arithmetic, draft protection and recovery rules remain in production. No fixture switch, fake save feedback or future activity API was ported. The pinned three font files remain self-hosted, without synthesized weights. The calendar title uses the available medium weight rather than the specimen's incidental browser-default bold.

The follow-up request also adds direct schedule arrows around the calendar, stepping one day or seven days according to the view. This is an explicit update to the final specimen's calendar-only schedule. Narrow content keeps the new controls and Add run below the full-width heading. All arrow SVGs now carry the specimen's own fill/stroke attributes, including section movement, calendar months and sidebar collapse. Public browser checks click the actual arrow graphics and verify saved section order.

## Direct comparison

Comparison used the immutable specimen and the running production branch, both rendered with Playwright Chromium 156.0.8078.4 at 390px and 1280px. The edit fixture matches its 07:00 interval run and 2/3/1 km sections at 6:45/5:45/7:00. This is disposable data, separate from training records.

For ten form roles, computed family, size, weight, line height, padding, border color/width/radius, background, opacity, gap and grid columns match the specimen at both widths. The relative boxes also match exactly:

- At 390px, date/time is 358px wide by 73px high at y=101; the date input is 173px by 48px at y=126; the first section is 358px by 152px at y=359; notes are 358px by 338px at y=978.
- At 1280px, date/time is 640px by 73px at y=101; the date input is 312px by 48px at y=126; the first section is 640px by 152px at y=359; notes are 640px by 338px at y=978.

These positions are relative to the form content, excluding the study's wrapper controls and the production sidebar. The source date field was focused in historical captures; focus rings depend on interaction state.

The production navigation edge uses a real 3px border in place of the specimen's shadow, with compensated padding so normal placement matches. In forced colors it remains visible as ButtonText. Focus outlines and native control semantics remain intact. The short-viewport footer fallback and enlarged-action wrapping protect operation without changing ordinary geometry.

## Rendered evidence

- [Desktop edit](redesign/form-edit-desktop.png), [phone edit](redesign/form-edit-phone.png), [desktop create](redesign/form-create-desktop.png), [phone create](redesign/form-create-phone.png)
- [Desktop Week](redesign/schedule-week-desktop.png), [phone Week](redesign/schedule-week-phone.png), [desktop Day](redesign/schedule-day-desktop.png), [phone Day](redesign/schedule-day-phone.png)
- [Calendar](redesign/schedule-calendar-phone.png), [loading](redesign/form-initial-loading-phone.png), [read failure](redesign/form-initial-failure-phone.png), [saved-target confirmation](redesign/form-delete-confirmation-phone.png), [pending deletion](redesign/form-pending-delete-phone.png), [uncertain save](redesign/form-uncertain-save-phone.png)
- [Phone section arrows after moving a loaded section up and back down](redesign/form-section-arrows-phone.png)

Final checks and independent Standards/Spec results are recorded in [integrated acceptance](redesign-acceptance.md). Physical-phone software keyboard/touch/hardware safe areas, screen-reader review and maintainer visual acceptance remain open. Future stretching, yoga and strength remain outside the current run-only implementation.
