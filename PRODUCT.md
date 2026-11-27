# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Arnaud uses Aweille to plan and review his running training. The browser must work on phone and desktop. The initial design study covers the weekly schedule and run form, as confirmed on October 17, 2026.

## Product Purpose

Keep an editable running schedule, preserve planned targets separately from actual results, and let an external trainer agent read and manage training through the API.

## Operating Context

Arnaud agrees on training with an external agent, then reviews and changes planned runs in the browser. Training reviews happen on request. The browser and trainer use the same API.

## Capabilities and Constraints

The implemented browser supports Day/Week viewing and planned-run creation, editing, and permanent deletion. A planned run has a date, an optional time, a run type, ordered sections with distance and pace, and separate personal and trainer notes. Preserve exact units, section order, draft recovery, keyboard access, and existing save, deletion confirmation, and recovery behavior during visual work.

Future scope includes stretching, strength/bodyweight training, and yoga alongside running. Arnaud confirmed that each is an independent training block that can be scheduled, moved, or skipped separately, with several blocks on the same day. Timed blocks come first in chronological order, followed by untimed blocks. The design must accommodate this; these additional kinds and skipping are not implemented by the current run API. See [training blocks](docs/design/training-blocks.md).

The existing frontend uses Jinja2 templates, CSS, and small JavaScript files with FastAPI. The design study keeps this stack and existing workflows. See [README.md](README.md) for implemented capabilities and intended later work, and [CONTEXT.md](CONTEXT.md) for domain terms.

## Brand Commitments

Keep the name Aweille and functional, direct copy. Arnaud rejects the current visual design. The [Pinterest board](https://ca.pinterest.com/ark__no/aweille-ui/) is the reference for its replacement. He selected the precise watch, TimeMoto, and editorial references with selective color, rather than the colorful calendar, as the leading direction.

Arnaud selected IBM Plex Sans with IBM Plex Mono on October 17, 2026. [DESIGN.md](DESIGN.md#typography) defines their roles. Keep Aweille branding only in the approved collapsible sidebar, without a slogan. Arnaud selected the logo in the [logo exploration](https://github.com/ArnaudJalbert/aweille/issues/31); [DESIGN.md](DESIGN.md#logo) describes it.

## Evidence on Hand

The reference study inspected all twelve board images on October 17, 2026. [Reference notes](docs/design/visual-direction.md) record the observations and image sources. The [prototype](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-ui-prototype.html) uses explicitly illustrative planned runs, with no connection to saved training data.

Arnaud accepted the [schedule composition and interaction rules](docs/design/schedule-layout.md) and [sidebar integration](docs/design/sidebar-integration.md) on October 17, 2026. Day is the default, with a Week switcher, a time column, expanded Day details, and calendar navigation. The sidebar collapses fully on desktop and becomes a closed-by-default drawer on phones. The [form/deletion/recovery presentation](docs/design/run-form-presentation.md), [exact design tokens](DESIGN.md), and [implementation handoff](docs/design/implementation-handoff.md) complete the design specification. The [redesign map](https://github.com/ArnaudJalbert/aweille/issues/43) ends at that handoff; the milestone stays open for the three production PRs and browser, actual-phone, zoom and screen-reader acceptance. Planning completion does not mean the production redesign has shipped.

## Product Principles

- Make the week's planned runs easy to scan and inspect.
- Keep targets, results, personal notes, and trainer notes distinct.
- Let the browser and external agent work with the same training records.
- Use the selected visual direction consistently without changing training behavior.
