---
version: alpha
name: Aweille
description: Precise running plans on pale surfaces with selective color.
colors:
  primary: "#a8d5a2"
  primary-hover: "#96c98f"
  paper: "#f0f1ea"
  panel: "#fafbf6"
  ink: "#202b28"
  muted-ink: "#59625c"
  line: "#c2c8bd"
  strong-line: "#788176"
  error: "#9d3027"
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
    padding: "10px 16px"
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

Draft v0.1, October 17, 2026. Arnaud selected a precise appearance with selective color, led by the watch, TimeMoto, and editorial references in his [Pinterest board](https://ca.pinterest.com/ark__no/aweille-ui/). The existing application's design is explicitly rejected. This document describes the [new prototype](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-ui-prototype.html), not the current application.

The confirmed direction uses pale surfaces, dark typography, measured alignment, and restrained emphasis. IBM Plex Sans and IBM Plex Mono are the selected typefaces. The other exact tokens above remain proposed values used by the specimen and subject to visual review. The references establish a direction, not exact colors or component geometry. [Reference notes](docs/design/visual-direction.md) distinguish observations from decisions.

Make a running plan readable through alignment, type, and space. Reuse the same controls on every screen. Measurement graphics may add information when their units and purpose are explicit. Avoid imagery or decoration that competes with the task.

## Colors

Paper is the main surface; panel distinguishes editable fields. Ink carries primary content, with muted ink for secondary content that must remain readable.

Arnaud requested a lighter green in place of orange on October 17, 2026. The current run-form study uses light green for the main action and sparingly on meaningful selection or state. Use ink text on green. The proposed values are `#a8d5a2` and `#96c98f` on hover, pending visual review. Ordinary content and inactive days stay neutral. Earlier prototype captures retain the previous orange trial.

Line separates rows and related sections. Strong line outlines controls. Error text names the problem in words, and focus remains visibly distinct from selection. Color alone never communicates a run type, error, or saved state.

The secondary and error colors have defined roles; they are not extra brand accents. Do not assign a different decorative color to every day or run.

## Typography

Use IBM Plex Sans for the name, headings, labels, notes, and buttons. Use IBM Plex Mono with tabular numerals for dates, times, distances, and paces. Arnaud selected this pairing on October 17, 2026, after reviewing the font comparison. The typefaces are a design choice, not an identification of the fonts in the Pinterest references.

The [font comparison](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-font-options.html) retains the IBM Plex, Geist, and Space Grotesk alternatives as reference. [Selection notes](docs/design/font-options.md) record the chosen roles and sources. The layout prototype embeds the selected fonts so its appearance does not depend on locally installed typefaces. Actual-device rendering remains an implementation check.

Keep headings in sentence case. Prefer ordinary readable letters and numerals. Monospaced data does not imply terminal prompts or technical jargon in navigation.

The specimen uses a heading size of 26px in its narrow viewport treatment and 28px otherwise. Section headings are 18px. Prose and editable fields use the body token. Secondary labels may use 12px to 14px, but never hide essential information in faint or compressed text.

## Layout

Use a consistent alignment grid and fine horizontal rules. Group a label closely with its control; separate different tasks more generously. Notes wrap naturally without losing their personal/trainer labels.

The week study compares two structures: a complete weekly log and a selected day with a week index. Neither is yet the canonical page composition. Keep this choice local to the weekly screen rather than turning it into a universal layout rule.

The [approved navigation](https://github.com/ArnaudJalbert/aweille/issues/29) is a desktop sidebar that can collapse completely and a mobile overlay drawer that starts closed. Keep a reopen control, mobile dismissal controls, focus containment and return, and Aweille branding only in the sidebar without a slogan. The study's top branding does not override this requirement. The [sidebar integration decision](https://github.com/ArnaudJalbert/aweille/issues/45) must reconcile it with the new screens; the earlier instruction to retain the old weekly appearance is superseded by this redesign.

On phones, move secondary information below primary content and keep the reading order intact. On larger containers, use columns for related fields and secondary navigation where useful. Never shrink a desktop canvas to fit a phone.

For the current trial, controls have at least 44px height, fields have at least 46px height, and focus uses a 3px outline with a 3px offset. The two-column container threshold is 560px of available content width. These are specimen measurements to validate, not a completed device compatibility promise.

## Elevation & Depth

Keep the interface flat. Use surface tone, spacing, and one-pixel rules to distinguish regions. The prototype does not use offset block shadows, gradients, or layered floating cards. Its rounded outer frame belongs to the review container, not the product's page geometry.

## Shapes

The trial control radius is small. Plain rows and tables do not need individual rounded containers. Circles or repeated marks can communicate a measured quantity or selected state when their meaning is clear.

Keep dot graphics optional. A dotted number display or chart must never replace a readable distance, pace, date, or control label. The first specimen deliberately tests the typography and layout before introducing a chart.

## Components

These are specimen components, not yet reusable production components.

- Buttons use the primary token for the main action and quiet outlined or underlined styles for secondary actions. Hover, focus, and disabled states stay recognizable.
- Fields have persistent labels, panel backgrounds, and control outlines. Distance and pace labels include units. The narrow layout keeps editable text at 16px.
- Planned-run rows keep day, run type, optional time, section targets, and notes distinct. Repeated sections stay individually ordered.
- A day groups zero or more independent training blocks. Give each block a distinct kind/name, optional time, relevant summary, and its own detail or action. Run sections stay nested within their running block. The [training-block design](docs/design/training-blocks.md) separates this future scope from the current run-only implementation.
- Schedule blocks use collapsible details, approved by Arnaud on October 17, 2026. Keep the kind/name, optional time, and concise summary visible; put sections and notes in the disclosure. Details start collapsed. Each block expands independently, and several may stay open together.
- Section editors keep distance, pace, and ordering actions together. The last section cannot be removed.
- Personal and trainer notes remain separate labeled text. Neither becomes a tooltip or an icon-only disclosure.
- Error and recovery messages preserve the draft and name the available next step. The prototype shows message specimens; the full loading, deletion confirmation, stale-write, uncertain-write, and missing-run interactions still require integration design.

Before application adoption, complete state coverage, keyboard and touch checks, real content extremes, and behavior verification against the current app. A working preview Save button does not demonstrate production save behavior.

## Do's and Don'ts

- Do preserve the selected precise, restrained direction across screens.
- Do use color for a specific action, selection, or state.
- Do keep values readable with explicit units and stable numeric alignment.
- Do preserve standard form controls, meaningful labels, keyboard focus, and existing recovery behavior.
- Do mark provisional design choices and illustrative training data.
- Don't carry the old colors, spacing, borders, or typography forward by default.
- Don't use the colorful calendar as authority for coloring every surface.
- Don't copy a watch dial, map, dot display, or progress ring simply because it appears on the reference board.
- Don't treat this draft as approval to reskin the live app or change its workflows.
