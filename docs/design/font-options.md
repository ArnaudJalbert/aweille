# Font options for Aweille

Compared on October 17, 2026, following Arnaud's positive review of the initial visual study. Arnaud selected the first option, IBM Plex Sans with IBM Plex Mono. The [interactive comparison](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-font-options.html) retains the alternatives with identical sample content and the proposed Aweille palette.

## Shortlist

The fit judgments below are ours, based on the reference board and rendered specimens.

| Pairing | Roles | Why consider it | Tradeoff |
| --- | --- | --- | --- |
| IBM Plex Sans + IBM Plex Mono | Sans for the name, headings, controls, and notes; Mono for measurement | Selected. Precise with enough warmth for a personal training tool | Its technical character is noticeable; keep prose in Sans |
| Geist + Geist Mono | Sans for the name and interface; Mono for measurement | A quieter, more neutral alternative | Less individual character in the name |
| Space Grotesk + IBM Plex | Space Grotesk for the name and headings; Plex Sans for interface text; Plex Mono for measurement | More distinctive lettering while retaining the first option's readable interface | Three families add visual and loading complexity; use the extra family only if its character earns its place |

[IBM's own documentation](https://www.ibm.com/design/language/typography/typeface/) describes the Sans and Mono subfamilies, weights, and extended Latin language coverage, including French. Its [repository](https://github.com/IBM/plex) supplies source files and web formats and describes Plex's use in interfaces.

[Vercel's Geist repository](https://github.com/vercel/geist-font) describes Geist Sans and Geist Mono as companion typefaces, with Swiss typography among its influences. Vercel notes [differences between distribution methods](https://vercel.com/font), so production should use the specific tested files rather than assuming every distribution has identical glyph features.

[Florian Karsten's Space Grotesk repository](https://github.com/floriankarsten/space-grotesk) describes it as a proportional adaptation of Space Mono and documents its language support and SIL Open Font License.

## What the specimen checks

The name and headings use the same size and weight across candidates. Interface text stays at 16px; table measurements use 14px with tabular numerals. Explicit unit labels remain separate from font choice.

The comparison includes paces, distances, small labels, notes, and editable fields. The glyph line tests zero versus capital O, one versus capital I and lowercase l, and French text with accents and the œ ligature. French is a coverage probe, not a decision to translate the interface.

The preview embeds Latin and Latin Extended WOFF2 files from Google Fonts, including the relevant copyright notices and OFL texts under its credits disclosure. It runs without a font service connection or installation on the user's computer. The specimen requests regular, medium, and semibold sans weights and regular mono. Italics and broader script coverage have not been evaluated.

The selected pairing is recorded in the [design tokens](../../DESIGN.md#typography) and applied to the [layout prototype](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-ui-prototype.html). The browser implementation now uses the pinned production files below; [integrated verification](../verification/redesign-acceptance.md) records loading/fallback and pending manual acceptance. Switching to another pairing inside the comparison remains a local preview and does not change the recorded decision.

## Production files

Arnaud accepted three unchanged, complete, self-hosted WOFF2 files through [Finalize design tokens and implementation handoff](https://github.com/ArnaudJalbert/aweille/issues/47). Copy these exact upstream files and both complete licence notices into the application's static font directory in the first production PR. No npm runtime dependency, external font service, subset generation, or embedded prototype font is needed.

| Family/weight | Immutable file | Bytes | Internal version |
| --- | --- | --- | --- |
| Sans 400 | [IBMPlexSans-Regular.woff2](https://github.com/IBM/plex/blob/1da12f02587b630c07e92692d21492d722f53614/packages/plex-sans/fonts/complete/woff2/IBMPlexSans-Regular.woff2) | 63,020 | 3.005 |
| Sans 500 | [IBMPlexSans-Medium.woff2](https://github.com/IBM/plex/blob/1da12f02587b630c07e92692d21492d722f53614/packages/plex-sans/fonts/complete/woff2/IBMPlexSans-Medium.woff2) | 66,740 | 3.005 |
| Mono 400 | [IBMPlexMono-Regular.woff2](https://github.com/IBM/plex/blob/2f9ba1b25957d958db71a849e85d72e3ecfb845a/packages/plex-mono/fonts/complete/woff2/IBMPlexMono-Regular.woff2) | 49,248 | 2.005 |

Sans comes from `@ibm/plex-sans@1.1.0`, source commit `1da12f02587b630c07e92692d21492d722f53614`. Mono comes from `@ibm/plex-mono@2.5.0`, source commit `2f9ba1b25957d958db71a849e85d72e3ecfb845a`. Package version and font internal version are different identifiers. Total font payload is 179,008 bytes before HTTP overhead.

Retain [Sans LICENSE.txt](https://github.com/IBM/plex/blob/1da12f02587b630c07e92692d21492d722f53614/packages/plex-sans/LICENSE.txt) and [Mono LICENSE.txt](https://github.com/IBM/plex/blob/2f9ba1b25957d958db71a849e85d72e3ecfb845a/packages/plex-mono/LICENSE.txt) alongside the distributed files, using distinct names such as `LICENSE-plex-sans.txt` and `LICENSE-plex-mono.txt`. Both contain the SIL Open Font License 1.1, IBM copyright and reserved font name Plex. Keep their text intact and keep this provenance link with the copied assets.

Use three explicit normal-style `@font-face` declarations with the corresponding weight, same-origin URLs and `font-display: swap`. Family fallbacks are `"IBM Plex Sans", Arial, sans-serif` and `"IBM Plex Mono", monospace`. No italic or additional weight is required; use 500 for Sans emphasis instead of synthesized 600/700. No local-font override should substitute unknown bytes for the pinned files. Ordinary static-file serving is sufficient; avoid a new font loader or asset-build system.

These complete files cover the current English interface and French notes. Direct inspection verified the requested weights and every character in `Élève à Montréal, cœur, Œuvre, Noël, façade, où, 0123456789 12.345 km 4:05 min/km − + /`. This does not promise all scripts or replace real rendering/fallback checks. [IBM's typeface guidance](https://www.ibm.com/design/language/typography/typeface/) documents its language coverage and recommends the repository distribution.

SHA-256 checksums for unchanged-file verification:

```text
ba711a3085ff9f27440b6b9c4550cfc47c97bf36591d5da958b975bb3add8c1a  IBMPlexSans-Regular.woff2
5660f8a658f8bb50dbc005232f885eadffd2bc1c235c4f6fbb63469d1f9cde6d  IBMPlexSans-Medium.woff2
ba204497f16b6d334cee9d1e963a831b73e3a56e1d6300a8489d18df7214b350  IBMPlexMono-Regular.woff2
```

Implementation checks must verify same-origin loading, actual computed families/weights, accented notes and exact measurements on all three screens, and readable fallback with font requests blocked. Include wrapping, zoom, long values, and sticky actions in both loaded and fallback states. The planning ticket verified binary/coverage inspection. The [implementation record](../verification/redesign-acceptance.md) adds same-origin browser loading/fallback checks; physical-device rendering remains pending.
