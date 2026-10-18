# Sidebar integration

Arnaud approved this integration on October 17, 2026 through [Fit the approved sidebar into the new design](https://github.com/ArnaudJalbert/aweille/issues/45). It extends the earlier full-sidebar choice to the accepted schedule. The browser implementation follows this decision; [integrated verification](../verification/redesign-acceptance.md) records evidence and remaining manual acceptance.

## Selected geometry and placement

| Part | Selected behavior |
| --- | --- |
| Desktop sidebar | 224px, initially expanded, fully collapsible with no residual icon rail |
| Drawer threshold | Below 900px of available application width |
| Phone drawer | Initially closed; up to 280px wide, leaving at least 44px of backdrop |
| Content spacing | 24px desktop padding, 16px in drawer mode; schedule capped at 960px |
| Menu control | Beside Week/Day in the schedule toolbar and beside create/edit headings |
| Branding | Aweille text in Plex Sans, only inside the sidebar, without a slogan |
| Navigation entries | Schedule active; Run history and Trainer are disabled placeholders |

At exactly 900px of available width, the expanded sidebar leaves 628px for content after padding. Use the available application width rather than browser identity to select drawer behavior. Collapsing the desktop sidebar frees its full column while retaining a reopen control.

Keep Today at the end of the schedule toolbar. Calendar and Add run stay beside their date heading. Preserve the [accepted schedule](schedule-layout.md), including Day as default, the time column, view-specific disclosure defaults, multiple runs per day, and no schedule arrows.

## Navigation and focus

The phone drawer is modal, contains keyboard focus, and prevents background interaction and scrolling. Close, backdrop, and Escape dismiss it and return focus to its initiating menu control. Selecting Schedule dismisses it and focuses the selected schedule heading.

Desktop collapse returns focus to the visible menu control. Navigation toggles preserve selected dates, view, disclosures, and form values. A drawer closes before Escape can dismiss a form behind it. Leaving a changed form through Schedule must preserve the existing draft-protection behavior, including keeping the draft when discard is declined.

Switching to a narrow layout closes the drawer. Returning to desktop restores the in-memory desktop collapse choice. Reload uses the default sidebar state; no saved navigation preference is implied.

## Form boundary and implementation

The integration study places create/edit in the content column to exercise navigation beside forms. Approval settles the sidebar, menu placement, and surrounding spacing. The subsequent [approved form decision](run-form-presentation.md) settles form geometry, section controls, sticky actions, deletion confirmation, validation, pending writes, and recovery presentation. The sidebar specimen alone does not settle those choices or replace production behavior contracts.

Reuse [Add responsive collapsible left navigation from variant A](https://github.com/ArnaudJalbert/aweille/issues/29) for implementation. Extend acceptance to edit and deletion/recovery flows, and replace its old appearance/navigation assumptions with the selected schedule. Keep prototype controls, fixtures, local save feedback, and comparison assets off main.

The [approved study, sixteen screen captures, run instructions, and verification limits](https://github.com/ArnaudJalbert/aweille/blob/76e8ade669d2932542a336eeabd9e06cc63213f1/docs/design/sidebar-integration-review.md) preserve the primary source on the disposable branch. Browser checks covered 320px through 1280px, an exactly 900px container, desktop collapse, drawer dismissal and focus, dirty-draft keep/discard, local creation, and calendar selection. Physical-phone, screen-reader, actual browser zoom, and production integration checks remain for implementation acceptance.
