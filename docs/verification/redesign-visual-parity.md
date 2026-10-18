# Redesign visual correction

Arnaud's October 18 review found that the first implementation did not reproduce the approved presentation. The behavioral suite and previous reviews missed visible omissions. This correction compares rendered screens directly with the approved screenshots, as well as repeating behavior checks.

## Primary sources

- [Approved sidebar/schedule study and captures](https://github.com/ArnaudJalbert/aweille/blob/76e8ade669d2932542a336eeabd9e06cc63213f1/docs/design/sidebar-integration-review.md), particularly its desktop Week and phone Week screens.
- [Approved form/state study and captures](https://github.com/ArnaudJalbert/aweille/blob/a336dcbe2be9c2d08dd5f3c3cbcf2cc04848b9bd/docs/design/run-form-review.md), particularly its desktop edit-ready screen.
- [Consolidated tokens and responsive rules](../../DESIGN.md), which supersede older specimen colors, typography, target sizes and paired-field thresholds.

## Corrected omissions

The foundation PR restores the Training group, navigation line icons, Planned captions, green active indicator, and desktop collapse control inside the sidebar. Menu/collapse icons match the specimen while retaining their names, focus behavior and 44px targets.

The schedule PR restores the Training schedule label, Week/Day ordering, right-aligned line-icon calendar, 116px desktop day column, timeline lines and circle markers, Running labels, multiple-run counts, plus/minus disclosures and flat sections/notes. Phone weekdays and dates use two lines. Day has one date heading. The calendar names its day/week context and uses the compact specimen geometry.

The form PR restores the short Add run/Edit run headings, compact spacing, legends interrupting section rules, quiet Remove/Add section actions, icon-only named up/down actions, right-aligned Optional labels and taller notes. The fields/helper and create/edit write controllers retain their existing behavior. No recovery policy, API, storage or dependency changes accompany the presentation correction.

## Render comparison

Playwright Chromium 156.0.8078.4 rendered the corrected application at 1280px and 390px with no page errors or overflow. The desktop edit fixture uses the approved specimen's 07:00 interval run with 2/3/1 km sections at 6:45/5:45/7:00, making the spacing and control comparison direct. All captures use a separate disposable database. Capturing failure/pending states intercepted writes; no capture sent a write to storage.

- [Corrected desktop Week](redesign/schedule-week-desktop.png) and [phone Week](redesign/schedule-week-phone.png)
- [Corrected desktop Day](redesign/schedule-day-desktop.png) and [phone Day](redesign/schedule-day-phone.png)
- [Contextual calendar](redesign/schedule-calendar-phone.png)
- [Desktop edit](redesign/form-edit-desktop.png), [phone edit](redesign/form-edit-phone.png), [desktop create](redesign/form-create-desktop.png) and [phone create](redesign/form-create-phone.png)
- Refreshed [loading](redesign/form-initial-loading-phone.png), [read failure](redesign/form-initial-failure-phone.png), [saved-target confirmation](redesign/form-delete-confirmation-phone.png), [pending deletion](redesign/form-pending-delete-phone.png) and [uncertain save](redesign/form-uncertain-save-phone.png)

The run-only schedule intentionally omits the studies' future stretching, yoga and strength fixtures. Green actions, 13px buttons, 14px time labels, 46px fields, readable disabled controls and 4px radii follow the consolidated handoff. The active sidebar uses the required panel surface and real 3px ink boundary with a supplementary green stripe, including a visible boundary in forced colors. Disabled section/navigation controls retain panel surfaces. Below 560px of content, target/date/note fields stack even where an older specimen capture paired them. Native details, exact values and accessible labels remain present.

The corrected schedule, create and edit screens were rechecked in native Firefox 158.0 at actual 200% browser zoom on October 18. The browser indicator confirmed 200%, navigation reflowed to a closed drawer, fields stayed readable, and the edit footer's Cancel returned to the schedule heading. No write was sent. Zoom was reset and only the temporary tab closed.

## Verification

The corrected foundation and schedule layers passed their complete required checks with 350 and 356 tests. Added assertions extend existing public-browser scenarios to protect the restored sidebar control/hierarchy, single Day heading, Running label, rendered timeline and quiet/icon section actions. Final combined checks and the separate Standards/Spec review results are recorded in [integrated acceptance](redesign-acceptance.md).

Physical-phone software keyboard/touch/hardware safe areas and screen-reader review remain pending. These visual comparisons do not close #51 or the redesign milestone.
