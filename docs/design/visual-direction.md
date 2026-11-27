# Aweille visual direction

Initial study, October 17, 2026. Arnaud explicitly rejected the current design, selected a precise appearance with selective color, and confirmed the weekly schedule and run form as the first test surfaces on phone and desktop.

## Reference reading

Source: [Aweille UI on Pinterest](https://ca.pinterest.com/ark__no/aweille-ui/). All twelve saved images were inspected at their available original resolution. The numbering below records this inspection order, not a permanent Pinterest ordering. Recommended images below the board's twelve pins were excluded. Creator and font attribution are not inferred from appearance.

| Reference | Observed characteristics | What it suggests for Aweille |
| --- | --- | --- |
| [Calendar, 1](https://i.pinimg.com/originals/4c/cd/e6/4ccde66490807b002662611b99031ddf.jpg) | Pale ground, large dates, many colored panels | Useful date hierarchy; broad coloring is not the selected lead |
| [Project app, 2](https://i.pinimg.com/originals/c0/af/90/c0af90194af235c6a76550c847f5d687.jpg) | Quiet neutrals, outlined icons, small navigation | Legible secondary controls; its card grid is not a requirement |
| [Revenue dots, 3](https://i.pinimg.com/originals/93/de/af/93deaf59697c99ea6fe6bdd56365b9df.jpg) | Monochrome dot columns, precise numerals, sparse rules | A possible measured-data vocabulary, with units and readable values |
| [Employment chart, 4](https://i.pinimg.com/originals/e7/df/82/e7df822989ca50a7efaae98dc1d81144.png) | Repeated units, categorical color, explicit legend | Color and marks should carry a defined meaning |
| [Publishing archive, 5](https://i.pinimg.com/originals/b6/2c/08/b62c08bec7dfec47f20662762d786875.jpg) | Compact grid, typographic labels, visible rules | Consistent alignment and editorial information hierarchy |
| [Berlin spread, 6](https://i.pinimg.com/originals/c3/ed/9e/c3ed9eda801bfd49a3bcdbd13303bc3f.jpg) | Open page, fine rules, small multiples, selective red | Flat surfaces, deliberate spacing, an accent with a specific job |
| [Text menu, 7](https://i.pinimg.com/originals/02/c0/ec/02c0ec1a04ee42d6e0bc526f5f4d44b2.jpg) | Monospaced text, clear vertical rhythm | Technical typography as a reference; normal controls keep ordinary labels |
| [Watch, 8](https://i.pinimg.com/originals/57/bf/d0/57bfd0229723ccbeae0bf30a0f66c298.png) | Fine outlines, aligned measurements, minimal charts | Distances and paces get stable alignment and explicit units |
| [Dot clock, 9](https://i.pinimg.com/originals/de/2d/23/de2d23fdb73a7874e5bf415b74e13bf5.jpg) | Warm ground, dark type, dot-matrix display | An optional data motif; avoid making essential numbers harder to read |
| [Transit map, 10](https://i.pinimg.com/originals/9f/c3/46/9fc3468700cf35950c7feeee85450ef4.jpg) | Repeated hexagons encode a measured quantity | Reference for later visualization, not a reason to add maps |
| [TimeMoto, 11](https://i.pinimg.com/originals/67/17/4d/67174d87f651b6fb6be886f682cada3f.png) | Pale gray-green, near-black type, orange action, generous space | Strongest reference for restrained surfaces and selective emphasis |
| [Control panel, 12](https://i.pinimg.com/originals/b4/65/6a/b4656a4f64e817f980e809571154fe9e.jpg) | Pale green, outlined controls, large tabular measurements | Useful measurement treatment; avoid decorative gauges without data |

These are our visual interpretations. Saving an image does not imply approval of every detail in it.

## Confirmed direction and proposed details

The selected direction combines restrained surfaces, precise typography, and selective color. IBM Plex Sans and IBM Plex Mono are the selected typefaces. The proposed orange accent, spacing, and corner values remain trial choices shown in the prototype. The board does not establish exact fonts or color values.

The first [DESIGN.md](../../DESIGN.md) documents the prototype's actual values. It is a draft system, not a description of the existing application. [PRODUCT.md](../../PRODUCT.md) records the product constraints separately.

## First surface study

The [standalone prototype](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-ui-prototype.html) compares two compositions within the selected world. The disposable studies are preserved on `chore/aweille-design-study`, outside the main-branch documentation. See the [reference checkout instructions](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/PROTOTYPE.md) to run them locally. The links use an immutable commit so later explorations cannot change this evidence.

- `?variant=log&screen=week` shows the entire week as aligned, ruled rows. This is the initial recommendation because all days remain visible together.
- `?variant=focus&screen=week` puts a selected day's run beside a compact week index. It gives section details more space but requires changing the selected day to inspect other runs.
- `?screen=form` shows the same run form under either composition. Date, time, type, ordered sections, and both notes remain visible.

The narrow-width switch tests the same content in a phone-sized container. Form fields and sample sections are editable only in memory. Saving reports a preview message and never calls Aweille. The reference images are linked as evidence, not shipped as interface assets.

Review which week composition is easier to read, whether the orange feels right, and whether the typography feels precise without becoming cold or cramped. No composition has been selected yet. Loading, validation, deletion confirmation, stale-write, uncertain-write, and missing-run states still need design and integration checks against the real application before adoption.

The initial specimen was rendered at 320px, 360px, 728px, and 1280px. Both layouts and the form fit the checked narrow and wide viewports without horizontal overflow. Browser checks covered layout switching, selecting an empty day, section addition/removal/reordering, and preview-only submission. Main text, secondary text, error text, and primary-button text meet a calculated 4.5:1 contrast ratio on their proposed backgrounds. These checks do not establish complete accessibility, actual-device compatibility, or production behavior.

## Multiple blocks per day

The layout now groups a list of independent training blocks under each date. Use `?training=mixed` to show the future mixed-training examples; `?training=mixed&variant=focus` opens Wednesday with stretching, an interval run, and yoga. The Add block chooser adds illustrative entries locally, including a second entry of the same kind. Each mixed-training block has its own disclosure for details.

Arnaud confirmed independent scheduling, moving, and skipping, with timed blocks first and untimed blocks last. These are future product rules. The [training-block design](training-blocks.md) records the distinction from run sections and the current production implementation. The prototype demonstrates grouping and local addition, not production editing or lifecycle operations for non-running blocks.

Arnaud approved the collapsible per-block details on October 17, 2026. Preserve the visible block summary and independent expansion in the design. He explicitly requested design adaptation only; production implementation remains deferred.

## Font exploration

Arnaud liked the initial study and asked for font options. The [font comparison](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-font-options.html) holds the sample content, sizes, and colors constant while testing three pairings. He selected IBM Plex Sans with IBM Plex Mono on October 17, 2026. [Font notes](font-options.md) record the decision, sources, and remaining checks. The layout study now uses that pairing; the application remains unchanged.

## Planning handoff

The [running-app redesign map](https://github.com/ArnaudJalbert/aweille/issues/43) records the accepted [schedule composition](schedule-layout.md), [sidebar integration](sidebar-integration.md), and [form/deletion/recovery presentation](run-form-presentation.md). Day starts expanded and Week collapsed, superseding the initial all-collapsed specimen. The accepted [exact tokens](../../DESIGN.md) use light-green main actions and a lighter red Delete run button across schedule and forms. The [implementation handoff](implementation-handoff.md) settles production font files, shared boundaries, three ordered PRs and acceptance. Production and manual device/accessibility acceptance remain unimplemented.

The [approved sidebar](https://github.com/ArnaudJalbert/aweille/issues/29) still requires full desktop collapse, an initially closed mobile overlay drawer, accessible dismissal/focus handling, and Aweille branding only inside the sidebar without a slogan. Integrate those preferences with the new design rather than copying the study's top branding. The earlier requirement to retain the existing weekly appearance is superseded. The [logo exploration](https://github.com/ArnaudJalbert/aweille/issues/31) settled the logo; see [DESIGN.md](../../DESIGN.md#logo).

## Workflow used

Followed the published [Impeccable skill](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/SKILL.md), especially its redesign, Operate, product-context, and document guidance. The local launcher and automatic detectors were not installed or run. Used the prototype skill for the separate visual comparison. No new persistent skill or application route was installed.
