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
