# Shared foundation and sidebar verification

Layer 1 for [#29](https://github.com/ArnaudJalbert/aweille/issues/29), following the merged [#52 handoff](https://github.com/ArnaudJalbert/aweille/pull/52).

```text
base shell + pinned fonts + common tokens
  -> existing weekly schedule
  -> create controller + raw draft/pending leave guard
  -> edit controller + dirty/pending leave guard
```

The shared sidebar measures application width with ResizeObserver. Its desktop choice lives only in the current document. Navigation from a form dispatches an intent to that form's controller so the controller retains ownership of drafts and pending requests. Creation compares raw field values in section order against the initially rendered form, including its prefilled date. Invalid partial entries count as changes.

Automated public-browser checks cover all three screens at 320, 390, 899, 900 and 1280 CSS px, font loading and blocked-font fallback, French notes, desktop collapse/reopen, drawer focus trapping/Escape, resize restoration and a constrained application inside a wider viewport. At exactly 900px the expanded shell is 628px wide; collapse frees all 224px. A declined Schedule departure preserves an invalid create draft and its errors. Declining departure during a delayed creation leaves the request active and it completes once, without another submission.

The three WOFF2 SHA-256 checksums match [the pinned policy](../design/font-options.md#production-files). Both complete OFL notices ship beside the fonts. Sans 400/500 and Mono 400 use same-origin URLs, swap and Arial/monospace fallbacks, with font synthesis disabled.

Presentation assertions changed intentionally for sidebar-only branding, narrow stacked targets, readable disabled controls and the accepted palette. Existing API, exact-unit, ordering, revision, draft and recovery assertions remain.

Evidence captured with the T3 collaborative Chromium browser on macOS, October 17, 2026, using an isolated temporary SQLite database:

- [Desktop sidebar around the existing schedule](redesign/foundation-desktop.png)
- [390px drawer](redesign/foundation-drawer.png)

These are intermediate screens. Day/Week composition belongs to #50; the final fields/footer/loading presentation belongs to #51. Physical-phone, actual zoom and screen-reader acceptance remain pending and do not gate preparing those PRs.

Required checks passed on this layer: `uv run pytest`, `uv run ty check`, `uv run ruff check .`, `uv run ruff format --check .`, and `git diff --check`.

## Visual review correction

Arnaud's October 18 review exposed missing presentation from the [approved sidebar specimen](https://github.com/ArnaudJalbert/aweille/blob/76e8ade669d2932542a336eeabd9e06cc63213f1/docs/design/sidebar-integration-review/desktop-expanded.png). The correction restores the Training group, navigation icons, Planned captions, green active indicator and in-sidebar desktop collapse control. Menu and collapse controls use the specimen's line icons rather than text glyphs and retain 44px targets. Disabled entries keep readable contrast instead of the specimen's reduced opacity. The public navigation regression now exercises desktop collapse from the sidebar and its focus return as well as drawer dismissal.

The consolidated active state retains its panel surface and 3px ink indicator, with a supplementary green stripe. Disabled entries retain panel surfaces and readable ink. These handoff states supersede the older specimen's green-only selection and faded disabled entries.

The earlier images above predate this correction. Final corrected screenshots and comparisons belong to the forms/integration layer; behavior checks alone did not establish visual fidelity.
