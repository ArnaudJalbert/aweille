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

The selected pairing is recorded in the [design tokens](../../DESIGN.md#typography) and applied to the [layout prototype](https://github.com/ArnaudJalbert/aweille/blob/af16a8045c216c375d12a100ba6eed10c848eb1a/docs/design/aweille-ui-prototype.html). The production application has not been reskinned. Switching to another pairing inside the comparison remains a local preview and does not change the recorded decision.
