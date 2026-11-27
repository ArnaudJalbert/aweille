---
version: 1.0
name: Aweille
description: Precise running plans on pale surfaces with selective color.
colors:
  primary: "#a8d5a2"
  primary-hover: "#96c98f"
  paper: "#f0f1ea"
  panel: "#fafbf6"
  navigation-selection: "#e3e7dd"
  ink: "#202b28"
  muted-ink: "#59625c"
  line: "#c2c8bd"
  strong-line: "#788176"
  error: "#9d3027"
  destructive: "#bb4c43"
  destructive-hover: "#9d3027"
  focus: "#315d98"
typography:
  heading:
    fontFamily: '"IBM Plex Sans", Arial, sans-serif'
    fontSize: "28px"
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  body:
    fontFamily: '"IBM Plex Sans", Arial, sans-serif'
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: '"IBM Plex Sans", Arial, sans-serif'
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  measurement:
    fontFamily: '"IBM Plex Mono", monospace'
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  button:
    fontFamily: '"IBM Plex Sans", Arial, sans-serif'
    fontSize: "13px"
    fontWeight: 500
    lineHeight: "20px"
rounded:
  control: "4px"
spacing:
  xs: "4px"
  sm: "8px"
  compact: "12px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  section: "48px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "8px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.ink}"
  input:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
---

# Aweille design system

## Overview

Accepted implementation specification, following [Finalize design tokens and implementation handoff](https://github.com/ArnaudJalbert/aweille/issues/47). Arnaud approved the exact palette, type, geometry, production font policy, three-PR sequence, and acceptance requirements in that decision. The precise appearance with selective color comes from the watch, TimeMoto, and editorial references in his [Pinterest board](https://ca.pinterest.com/ark__no/aweille-ui/). The browser implementation applies this specification. The [integration record](docs/verification/redesign-acceptance.md) documents automated checks, actual desktop zoom and remaining manual acceptance; the implementation PRs remain open and no deployment is implied.

Use the exact values here across schedule, create, and edit. The [implementation handoff](docs/design/implementation-handoff.md) defines shared code boundaries, production PRs, and checks. [Reference notes](docs/design/visual-direction.md) and immutable studies preserve the evidence; this specification takes precedence where their older specimen values differ.

Make a running plan readable through alignment, type, and space. Reuse the same controls on every screen. Measurement graphics may add information when their units and purpose are explicit. Avoid imagery or decoration that competes with the task.

## Production visual reference

On October 18, Arnaud asked to reproduce the approved prototype's look in production. The [final green form specimen](https://github.com/ArnaudJalbert/aweille/blob/a336dcbe2be9c2d08dd5f3c3cbcf2cc04848b9bd/docs/design/run-form-prototype.html) is the visual reference for schedule, sidebar, forms and state treatments. This request supersedes the earlier handoff's narrower interpretations where they changed the specimen's appearance. Keep its paired date/time and section fields on phones, full-width stacked notes, Sans editable text, button typography/borders, selected navigation treatment and disabled-action appearance. Preserve real API writes, draft/revision/recovery rules, native semantics, visible focus and forced-color selection boundaries. Prototype fixtures, study controls and future activity kinds remain outside production.

On October 21, Arnaud requested Planned date above optional Start time in phone mode after testing on iPhone Safari. Stack those two fields in drawer mode, below 900px of available application width. Keep them paired on desktop and keep section distance/pace paired at every width. This supersedes only the specimen's phone date/time arrangement.

## Colors

Paper is the main surface; panel distinguishes editable fields. Ink carries primary content, with muted ink for secondary content that must remain readable.

Main actions use light green `#a8d5a2`, hover/active `#96c98f`, with ink text. This applies to Add run as well as Save. Delete run uses `#bb4c43` with white text, and keeps that fill on hover/active as in the prototype. Keep `#9d3027` for error text, invalid-field borders, and the outlined permanent-deletion confirmation action. Ordinary content and inactive days stay neutral.

Line separates rows and related sections. Strong line outlines controls. Error text names the problem in words, and focus remains visibly distinct from selection. Color alone never communicates a run type, error, or saved state.

| Role | Treatment |
| --- | --- |
| Primary action | Prototype green fill and matching border, ink text; Add run has a borderless 28px face; hover/active uses primary-hover |
| Secondary action | Transparent surface, ink text, strong-line border on framed actions; quiet/icon actions remain borderless; text links underline |
| Delete entry | Destructive fill and matching border, white text; retains its fill/border on hover/active |
| Permanent confirmation | Panel surface, error text and border, matching the prototype |
| Selected Day/Week or calendar date | Ink fill, panel text, semantic pressed state |
| Active sidebar entry | Prototype navigation-selection surface, ink text, 3px green boundary and `aria-current`; forced colors uses a real ButtonText boundary |
| Disabled controls | Prototype action fills with .45 action opacity, .65 for disabled navigation; no hover change. Draft inputs remain opaque ink on panel. Retain native disabled semantics |
| Pending write | Unavailable actions plus opaque readable draft inputs and Saving/Deleting progress, live announcement and busy semantics |
| Error or destructive notice | Panel surface, error text/leading rule and a named problem/action; retain draft text in ink |
| Neutral loading/recovery notice | Panel surface, ink text, strong-line leading rule, explicit next action |
| Keyboard focus | 3px focus outline, 3px offset; never remove it for selected/error states |

Use `--navigation-selection: #e3e7dd` for the prototype navigation selection/icon hover, alongside the existing `paper`, `panel`, `ink`, `muted-ink`, `line`, `strong-line`, `primary`, `primary-hover`, `destructive`, `destructive-hover`, `error`, and `focus` names as CSS custom properties. Add `--on-destructive: #fff` for Delete text and `--backdrop: #202b2866` for the drawer. The calendar uses the specimen's `#202b2877` backdrop and 8px dialog radius. No separate success, warning, or per-kind palettes are needed. A confirmed write returns to fresh schedule data; do not add fake save feedback or infer success from a color.

Calculated contrast is 12.85:1 for ink/paper, 5.55:1 for muted ink/paper, 3.55:1 for strong-line/paper, 5.87:1 for focus/paper, 6.40:1 for error/paper, 8.84:1 for ink/green, 7.69:1 for ink/hover green, and 4.97:1 for white/destructive. The lighter destructive red is only 4.37:1 against paper, so it cannot replace error text. Pale line/paper is 1.50:1 and green/paper is 1.45:1. The prototype uses labeled green actions and a tinted active navigation row; retain their semantics, focus outlines and forced-color boundaries. Verify rendered states, including panel surfaces and fallback/forced-color rendering, during implementation.

The secondary and error colors have defined roles; they are not extra brand accents. Do not assign a different decorative color to every day or run.

## Typography

Use IBM Plex Sans for the name, headings, labels, notes, and buttons. Use IBM Plex Mono with tabular numerals for displayed schedule dates, times, distances, and paces. Editable fields use Sans as in the prototype. Arnaud selected this pairing on October 17, 2026, after reviewing the font comparison. The typefaces are a design choice, not an identification of the fonts in the Pinterest references.

The [font comparison](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-font-options.html) retains the IBM Plex, Geist, and Space Grotesk alternatives as reference. [Selection notes](docs/design/font-options.md) record the chosen roles and sources. The layout prototype embeds the selected fonts so its appearance does not depend on locally installed typefaces. Actual-device rendering remains an implementation check.

Keep headings in sentence case, except the explicitly selected relative schedule titles such as This Week and Next Week. Prefer ordinary readable letters and numerals. Monospaced data does not imply terminal prompts or technical jargon in navigation.

| Role | Size / weight / line height |
| --- | --- |
| Page heading | Schedule 28px / 500 / 1.15, 26px below 560px content; form 28px / 500 / 1.2, 26px below 420px viewport; letter spacing -0.025em |
| Section heading | 18px / 500 / 1.5 |
| Run title and emphasis | 16px / 500 / 1.5 |
| Body and editable text | 16px / 400 / 1.5 |
| Labels, help, measurements | 14px / 400 / 1.5; Mono for measurements |
| Supplementary labels | 12px / 400 / 1.5; never the only statement of essential content |
| Buttons | Form actions and Add run 13px / 500 / 20px; schedule toolbar 16px / 400 / 1.5; calendar footer 15px / 400 / 1.5 |
| Sidebar logo | Lockup image, 28px tall |

Use Sans 400/500 and Mono 400 only. Map emphasis such as `strong` to 500 rather than synthesizing an unshipped bold weight. Keep field labels and notes in Sans; editable values use Sans at 16px. Never reduce essential text to fit a long value. The [production font policy](docs/design/font-options.md#production-files) pins three full self-hosted WOFF2 files, licences, and fallbacks.

## Layout

Use a consistent alignment grid and fine horizontal rules. Group a label closely with its control; separate different tasks more generously. Notes wrap naturally without losing their personal/trainer labels.

Arnaud accepted the schedule composition on October 17, 2026. Day is the default, with a Week switcher and Today shortcut. Use the compact time column for activities, a calendar icon for contextual day/week selection, relative headings with exact dates beneath, and previous/next arrows beside the calendar. Arnaud requested the direct arrows on October 18; they move by one day in Day and seven days in Week, superseding the earlier calendar-only navigation decision. On narrow content, keep the date controls and Add run in a row below the heading so every target remains 44px. The [schedule decision](docs/design/schedule-layout.md) specifies summaries, Add run placement, editing entry, disclosure defaults, and navigation state. The [approved form presentation](docs/design/run-form-presentation.md) specifies create/edit, deletion, and recovery states.

The [approved sidebar integration](docs/design/sidebar-integration.md) uses a 224px desktop sidebar, initially expanded and fully collapsible, and a closed-by-default overlay drawer below 900px of available application width. Place the menu control beside Week/Day and beside create/edit headings. Keep mobile dismissal controls, focus containment and return, and the Aweille logo only inside the sidebar, without a slogan. The earlier instruction to retain the old weekly appearance is superseded by the accepted schedule. Reuse the [existing navigation execution issue](https://github.com/ArnaudJalbert/aweille/issues/29); the [approved form presentation](docs/design/run-form-presentation.md) supplies form geometry and recovery rules.

On phones, move secondary information below primary content and keep the reading order intact. On larger containers, use columns for related fields and secondary navigation where useful. Never shrink a desktop canvas to fit a phone.

Controls have at least 44px targets in both dimensions where practical; fields use the prototype's 44px minimum and 10px padding, with native field sizing matching the specimen. Add run retains its compact 28px visible face inside a non-overlapping 44px target. Fields and framed buttons use a 4px radius; the compact Add run face retains the prototype's 3px radius. Borders and separators are 1px; error/notice leading rules and selection indicators are 3px. Focus uses the treatment above.

Use spacing tokens `--space-xs: 4px`, `--space-sm: 8px`, `--space-compact: 12px`, `--space-md: 16px`, `--space-lg: 24px`, `--space-xl: 32px`, and `--space-section: 48px`. Use `--radius-control: 4px`, `--target-min: 44px`, `--field-min: 44px`, `--schedule-max: 960px`, `--form-max: 640px`, and `--sidebar-width: 224px`. Keep font families/sizes/weights in a shared CSS type layer; do not build a token registry or JavaScript theme API.

Stack Planned date above Start time in phone/drawer mode, below 900px of available application width. On desktop, date/time use two equal `minmax(0, 1fr)` columns. Keep section distance/pace in two equal columns at every width, including 320px and 390px. Use 16px gaps, reduced to 12px below a 420px viewport. Notes form full-width vertical rows under a Notes heading. The schedule retains its content-based 560px day-column threshold and phone Add run placement. Sidebar mode still measures available application width. At 900px application width, the expanded sidebar leaves 628px content after 24px padding on both sides. Drawer mode uses 16px padding and the approved up-to-280px drawer with at least 44px backdrop.

Cap the form at 640px and schedule at 960px. Use natural wrapping, `min-width: 0`, and overflow wrapping for long values/notes. The footer keeps Cancel/Delete left and Save right in one row at 320px with normal text; shorten padding before shrinking text or targets. With enlarged text, permit action wrapping to preserve reading and operation. Keep the footer within the form width, add bottom content clearance, and include `env(safe-area-inset-bottom)` in its bottom padding. A software keyboard or short viewport must not trap the focused field behind it.

## Elevation & Depth

Keep the interface flat. Use surface tone, spacing, and one-pixel rules to distinguish regions. The prototype does not use offset block shadows, gradients, or layered floating cards. Its rounded outer frame belongs to the review container, not the product's page geometry.

## Shapes

The control radius is 4px. Plain rows and tables do not need individual rounded containers. The product has no rounded outer specimen frame. Circles or repeated marks can communicate a measured quantity or selected state when their meaning is clear.

Keep dot graphics optional. A dotted number display or chart must never replace a readable distance, pace, date, or control label. The first specimen deliberately tests the typography and layout before introducing a chart.

## Components

Implement these roles with the existing Jinja/CSS/JavaScript stack and the minimal shared boundaries in the handoff.

- Buttons use the prototype treatments and typography above. Add run and form actions retain 13px/500/20px text and at least 44px targets. Hover, focus, and disabled states stay recognizable.
- Fields have persistent labels, panel backgrounds, and control outlines. Distance and pace labels include units. The narrow layout keeps editable text at 16px.
- Planned-run rows keep day, run type, optional time, section targets, and notes distinct. Repeated sections stay individually ordered.
- A day groups zero or more independent training blocks. Give each block a distinct kind/name, optional time, relevant summary, and its own detail or action. Run sections stay nested within their running block. The [training-block design](docs/design/training-blocks.md) separates this future scope from the current run-only implementation.
- Schedule blocks use collapsible details, approved by Arnaud on October 17, 2026. Keep the kind/name, optional time, and concise summary visible; put sections and notes in the disclosure. Details start expanded in Day and collapsed in Week. Each view keeps its own manual disclosure choices until a week change or reload. Each block expands independently, and several may stay open together. See the [schedule decision](docs/design/schedule-layout.md).
- Section editors keep distance, pace, and ordering actions together. The last section cannot be removed.
- Personal and trainer notes remain separate labeled text. Neither becomes a tooltip or an icon-only disclosure.
- Create/edit replaces schedule content with a compact sticky footer. Cancel and red Delete run sit on the left, Save on the right. Delete opens an inline saved-target confirmation with Keep run focused first.
- Error and recovery messages preserve the draft and name the available next step. The [accepted state matrix](docs/design/run-form-presentation.md#state-to-presentation-matrix) covers loading, validation, pending writes, deletion, stale/uncertain results, reload, and missing state. Preserve existing behavior during implementation.

## Logo

Arnaud selected the logo on November 27, 2026, in the [logo exploration](https://github.com/ArnaudJalbert/aweille/issues/31). The mark is a single route stroke with a bowl and a smaller second rise, with no endpoint dot. It is a 13-unit monoline stroke with round caps in a 117 by 78 box. The wordmark is Outfit 500 at -0.02em tracking, converted to outlines so the application loads no extra font. Use ink only; no accent color is selected.

The files are in `packages/aweille/src/aweille/api/static/logo/`: `aweille-lockup.svg` for the sidebar, `aweille-favicon.svg` (paper mark on an ink tile) for the page icon, and `aweille-mark.svg` alone.

Before application adoption, complete state coverage, keyboard and touch checks, real content extremes, and behavior verification against the current app. A working preview Save button does not demonstrate production save behavior.

## Do's and Don'ts

- Do preserve the selected precise, restrained direction across screens.
- Do use color for a specific action, selection, or state.
- Do keep values readable with explicit units and stable numeric alignment.
- Do preserve standard form controls, meaningful labels, keyboard focus, and existing recovery behavior.
- Do identify illustrative training data and keep the captured studies separate from production.
- Don't carry the old colors, spacing, borders, or typography forward by default.
- Don't use the colorful calendar as authority for coloring every surface.
- Don't copy a watch dial, map, dot display, or progress ring simply because it appears on the reference board.
- Don't treat planning completion as evidence that the production redesign or device acceptance has shipped.
