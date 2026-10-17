# Run form and recovery review

Disposable study for [Define run-form, deletion, and recovery presentations](https://github.com/ArnaudJalbert/aweille/issues/46), October 17, 2026. Arnaud accepted three starting choices: the form replaces the schedule content area, Save/Cancel stay in a compact sticky footer, and Delete run is a red button immediately to the right of Cancel in the sticky footer. The latest placement request supersedes the earlier separate text action. Complete state presentation awaits review. Production remains unchanged.

## Run and review

```sh
python3 -m http.server 8768 --bind 127.0.0.1 --directory docs/design
```

Open [the form study](http://localhost:8768/run-form-prototype.html). It starts with an illustrative edit form. Screen switches between schedule, create, and edit. Form state selects an example; Form content offers a typical run, fourteen ordered sections with long notes, and targets larger than JavaScript's safe integer range. Content width offers narrow previews. All data is fixture memory and resets on reload. The HTML is self-contained with the selected Plex fonts and their licence notices.

Direct examples accept `mode=create`, `mode=edit`, or `mode=schedule`, with an optional `formstate` from the matrix below. Example parameters initialize the specimen; they are study controls rather than production route contracts. The schedule's existing view/date URL handling remains in the specimen.

## Form and actions

The form uses the approved sidebar and surrounding spacing. Its hierarchy is date/optional time, run type, ordered sections, and separate optional personal/trainer notes. Required fields stay labeled; inline errors sit beside their fields and the overall message names the next action. Known exact distance/pace conversion and section behavior reuse the current shared form helper, copied into the standalone study. The schedule formatter uses integer arithmetic for the large fixture, so saving/reopening it loses no precision.

Add section focuses the new distance input. Remove cannot remove the last section. Named up/down controls preserve order, disable at boundaries, and retain focus in the affected row. No drag-only ordering or new domain feature is introduced.

The footer groups Cancel and a solid red Delete run button on the left, with Save run/Save changes on the right. Delete run appears only when an existing run has loaded. The footer sticks to the viewport bottom while reading the form; fields have scroll clearance above it. The Delete run button opens an inline confirmation above the footer. The confirmation identifies the last loaded saved date/type, explains permanence, and warns about unsaved edits when present. Keep run gets focus first, preserves fields and validation feedback, and returns focus to Delete run. Pending deletion moves focus to its progress message.

Cancel and Schedule navigation protect a changed draft. The browser's ordinary dirty-page warning applies to reload/leave. Leaving during a pending request explicitly says that it does not cancel the request. The phone drawer opens above the form, contains focus, and dismisses before Escape can close a form behind it.

## State presentation matrix

The state selector holds pending/failure examples for inspection. Actual local Save/Delete briefly show progress and then change only the fixtures. Reload examples load the local baseline, not a server response. This gallery evaluates presentation and interaction; it does not prove production persistence, concurrency, or network recovery.

| Mode / state | Presentation and available action | Desktop | Phone |
| --- | --- | --- | --- |
| Edit / `ready` | Editable form and sticky actions | [View](run-form-review/desktop-edit-ready.png) | [View](run-form-review/phone-edit-ready.png) |
| Create / `ready` | Date prefilled; run type and required section targets blank | [View](run-form-review/desktop-create-ready.png) | [View](run-form-review/phone-create-ready.png) |
| Edit / `loading` | Loading status; hide fields and disable writes | [View](run-form-review/desktop-edit-loading.png) | [View](run-form-review/phone-edit-loading.png) |
| Edit / `load-failed` | Failed or unreadable initial load; Retry or return | [View](run-form-review/desktop-edit-load-failed.png) | [View](run-form-review/phone-edit-load-failed.png) |
| Edit / `missing-initial` | Run unavailable; return without an empty editor | [View](run-form-review/desktop-edit-missing-initial.png) | [View](run-form-review/phone-edit-missing-initial.png) |
| Edit / `pending-save` | Saving status, busy semantics, disabled competing edits/writes | [View](run-form-review/desktop-edit-pending-save.png) | [View](run-form-review/phone-edit-pending-save.png) |
| Edit / `validation` | Overall explanation, inline field error, first invalid input focus; retain values | [View](run-form-review/desktop-edit-validation.png) | [View](run-form-review/phone-edit-validation.png) |
| Edit / `oversized` | Reduce notes/sections; retain draft and allow correction | [View](run-form-review/desktop-edit-oversized.png) | [View](run-form-review/phone-edit-oversized.png) |
| Edit / `stale` | Saved run changed; keep draft, block writes, offer Reload saved run | [View](run-form-review/desktop-edit-stale.png) | [View](run-form-review/phone-edit-stale.png) |
| Edit / `reload-required` | Reload required without exposing HTTP headers or revision mechanics | [View](run-form-review/desktop-edit-reload-required.png) | [View](run-form-review/phone-edit-reload-required.png) |
| Edit / `uncertain-save` | Save may have succeeded; retain draft and require saved-state reload | [View](run-form-review/desktop-edit-uncertain-save.png) | [View](run-form-review/phone-edit-uncertain-save.png) |
| Edit / `reload-failed` | Keep the draft and blocked writes; Retry reload | [View](run-form-review/desktop-edit-reload-failed.png) | [View](run-form-review/phone-edit-reload-failed.png) |
| Edit / `reloaded` | Current saved values loaded; require review and a fresh explicit action | [View](run-form-review/desktop-edit-reloaded.png) | [View](run-form-review/phone-edit-reloaded.png) |
| Edit / `unchanged` | Show that values match the saved run; ordinary Save remains available | [View](run-form-review/desktop-edit-unchanged.png) | [View](run-form-review/phone-edit-unchanged.png) |
| Edit / `delete-confirm` | Inline saved-target confirmation; Keep run first; editing/Save disabled | [View](run-form-review/desktop-edit-delete-confirm.png) | [View](run-form-review/phone-edit-delete-confirm.png) |
| Edit / `pending-delete` | Deleting status, disabled competing actions, no undo or rollback promise | [View](run-form-review/desktop-edit-pending-delete.png) | [View](run-form-review/phone-edit-pending-delete.png) |
| Edit / `delete-rejected` | Run/draft retained; a retry starts a fresh explicit confirmation | [View](run-form-review/desktop-edit-delete-rejected.png) | [View](run-form-review/phone-edit-delete-rejected.png) |
| Edit / `uncertain-delete` | Deletion unconfirmed; retain draft and require reload, without direct delete retry | [View](run-form-review/desktop-edit-uncertain-delete.png) | [View](run-form-review/phone-edit-uncertain-delete.png) |
| Edit / `missing-after-write` | Run unavailable; keep draft for reference and disable writes without claiming who removed it | [View](run-form-review/desktop-edit-missing-after-write.png) | [View](run-form-review/phone-edit-missing-after-write.png) |
| Create / `uncertain-save` | Preserve the existing same-run/unchanged-values retry guidance and submitted-week inspection | [View](run-form-review/desktop-create-uncertain-save.png) | [View](run-form-review/phone-create-uncertain-save.png) |
| Create / `create-conflict` | Earlier attempt may have saved different data; inspect the submitted week rather than silently choosing a new identity | [View](run-form-review/desktop-create-create-conflict.png) | [View](run-form-review/phone-create-create-conflict.png) |
| Edit / `refresh-failed` | Save confirmed; schedule read failed; offer read retry without resending the write | [View](run-form-review/desktop-edit-refresh-failed.png) | [View](run-form-review/phone-edit-refresh-failed.png) |

Long-form scrolling examples are [desktop](run-form-review/desktop-long-scroll.png) and [phone](run-form-review/phone-long-scroll.png). Dirty deletion examples are [desktop](run-form-review/desktop-delete-draft.png) and [phone](run-form-review/phone-delete-draft.png), showing the saved target despite a different draft date.

The current study replaces orange accents with light green, as requested by Arnaud. Main actions and selection marks use `#a8d5a2`, with `#96c98f` on hover and dark ink text. Exact shades await visual review. Delete and errors retain their red treatment. Earlier schedule/sidebar studies are historical orange references.

## Verification and limits

Delete run now uses a lighter red `#bb4c43`. White text has 4.97:1 contrast. Error text and the outlined confirmation action retain their darker red.

The form buttons now share Add run's IBM Plex Sans, 13px size, 500 weight, and 20px line height. Footer, confirmation, section, and recovery actions use the same typography while retaining 44px minimum targets.

The green revision passed default/hover and disabled-state checks for Save/Add run at 320px, 390px, and 1280px without horizontal overflow. Dark ink contrast is 8.84:1 on the default green and 7.69:1 on hover. Delete stays red. All 48 form captures were refreshed without browser errors.

The footer revision passed at 320px, 390px, and 1280px: Cancel, red Delete run, and Save remain on one row without horizontal overflow. Buttons retain 44px height; Delete is hidden for creation and disabled during blocked/pending/confirmation states. Keep run retains the draft and returns focus to the moved Delete button. The state captures reflect this placement.

Playwright Chromium checks passed at 320px, 390px, 900px, 1024px, and 1280px across the edit-state matrix without horizontal overflow. Long-form checks verified that Save/Cancel remain visible while scrolling within the form. Interaction checks covered exact large-value save/reopen, add/remove/reorder boundaries and focus, validation retention/focus, saved-target deletion, Keep run with retained draft and field feedback, confirmed local deletion, cancelled and successful reload, failed-reload retention, create retry guidance versus edit reload requirements, confirmed-save/read-failure retry without duplicate creation, declined dirty-page reload, pending-deletion progress focus, and drawer Escape above a pending form. No runtime or console errors occurred in the 44 state captures and four additional long/dirty captures.

The T3 collaborative browser failed its snapshot step twice, most recently with `Preview automation snapshot timed out after 15000ms.` Verification used the repository's Playwright runner after that connection failure. Captures use 1280px and 390px browser viewports at 900px height. Physical devices, screen readers, actual browser zoom/software keyboards, safe-area behavior on hardware, and real HTTP/storage/concurrency recovery remain unchecked. Production browser contracts still need their own integration checks. No production test suite was rerun for this standalone HTML study.

## Existing behavior references

- [Planned-run editing/deletion browser contracts](planned-run-editing-and-deletion.md#browser-flows-and-acceptance)
- [Shared form helper](../../packages/aweille/src/aweille/adapters/web/static/run_form.js), [create flow](../../packages/aweille/src/aweille/adapters/web/static/create_run.js), and [edit/delete flow](../../packages/aweille/src/aweille/adapters/web/static/edit_run.js)
- Existing browser contracts in [creation](../../packages/aweille/tests/browser/test_run_creation.py), [editing](../../packages/aweille/tests/browser/test_run_editing.py), and [deletion](../../packages/aweille/tests/browser/test_run_deletion.py)
- [Approved schedule](https://github.com/ArnaudJalbert/aweille/issues/44) and [approved sidebar integration](https://github.com/ArnaudJalbert/aweille/issues/45)

Keep this decision open until Arnaud reviews the form and state examples. Authentication/session-expiry behavior remains owned by the existing authentication decision. No new API, saved draft store, automatic merge, background polling, or non-running editor is introduced.
