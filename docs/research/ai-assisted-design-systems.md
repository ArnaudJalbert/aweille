# AI-assisted design systems

Researched on October 17, 2026, from the linked official documentation, specifications and repositories. This is an options review, not an installation or a comparison of measured output quality. Product capabilities below describe the sources inspected; fit judgments and the proposed workflow are ours.

## Recommendation

For Aweille, start with **Impeccable, one versioned `DESIGN.md`, and the existing CSS/Jinja implementation**. Impeccable can help establish a direction, document it and consolidate repeated styles. The document gives later agent sessions explicit decisions to follow. Shared CSS and templates make those decisions real. This combination fits the existing frontend without introducing React.

A smaller alternative is Anthropic's `design-system` skill plus a manually maintained design document. Choose this if we want a short audit/document/extend procedure with fewer tools. Figma and Storybook become useful when we have design files or a component library worth connecting.

The distinction matters: a skill guides the agent's decisions; a design document preserves decisions; tokens and shared components implement them; MCP tools let agents inspect real assets. Adopting a component framework supplies another project's starting components. None of these jobs substitutes for all the others.

## What exists in Aweille

The [README](../../README.md#technology) specifies FastAPI, Jinja2, ordinary CSS and small JavaScript files. The [web adapter](../../packages/aweille/src/aweille/adapters/web) has three page templates and one stylesheet. [weekly.css](../../packages/aweille/src/aweille/adapters/web/static/weekly.css) already defines `--ink`, `--muted`, `--surface`, `--shadow`, `--positive` and `--negative`, alongside literal colors, spacing and typography. Buttons and focus outlines already share rules. These are repository observations.

Arnaud clarified after this research that he dislikes the current design and wants it replaced. The existing code provides workflow and technical context, not a visual system to preserve. The subsequent [reference study](../design/visual-direction.md) starts from his Pinterest board. A frontend migration remains separate from the visual-design decision.

## Options at a glance

These fit judgments summarize the sourced details below.

| Approach | Main job | Fit for Aweille | Main cost or limitation |
| --- | --- | --- | --- |
| Anthropic design-system and frontend-design skills | Audit consistency; explore visual direction | Good lightweight starting point | Instructions need persistent project decisions and rendered review |
| Impeccable, or interface-design | Establish, remember and refine a visual system | Strongest workflow fit | Choose one primary workflow; review generated rules |
| UI UX Pro Max | Search design guidance and generate a starting specification | Optional research aid | Catalog recommendations need product judgment |
| Google DESIGN.md and Stitch skills | Store exact tokens with rationale; extract an existing system | Strong document fit; Stitch optional | Format is alpha; extraction can preserve accidental styling |
| CSS variables, DTCG and Style Dictionary | Implement and exchange tokens | CSS now; token build tooling later | Additional generation pipeline needs maintenance |
| Storybook MCP | Expose component docs, examples and tests to agents | Later, if a library grows | Node tooling and framework-specific metadata support |
| Figma MCP and Code Connect | Design visually and map designs to actual code | Useful if Figma becomes part of the workflow | Seats, limits and maintained design/code mappings |
| shadcn MCP and registries | Discover and install existing component code | Poor default fit for this frontend | Default UI stack differs from Jinja/plain CSS |

## Skills for creating and maintaining the system

### Anthropic's two different skills

The official [design-system skill](https://github.com/anthropics/knowledge-work-plugins/blob/main/design/skills/design-system/SKILL.md) directly addresses this request. Its `audit`, `document` and `extend` procedures cover token coverage, naming, component variants, states, accessibility and migration. It can use connected design tools and documentation, but provides instructions and output templates without requiring them. This is suitable guidance for documenting Jinja components as well as JavaScript components. Its sample scores are an agent's assessment, not a deterministic conformance check.

The separate [frontend-design skill](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) emphasizes deliberate palette, type, layout and restrained visual identity. The inspected version asks for a compact token plan before implementation and screenshot critique where available. Use it when choosing a direction; our concern is that repeatedly inviting fresh visual invention can fight an established system unless the brief explicitly preserves it.

Both are Apache-2.0 licensed. [Design plugin license](https://github.com/anthropics/knowledge-work-plugins/blob/main/LICENSE), [frontend-design license](https://github.com/anthropics/skills/blob/main/skills/frontend-design/LICENSE.txt).

### Impeccable, with interface-design as an alternative

[Impeccable](https://github.com/pbakaus/impeccable) currently provides one skill, 24 commands, browser iteration and deterministic detectors. The detectors can run without an LLM or API key; agent-led work still uses the chosen agent. Its commands include `shape`, `critique`, `audit` and `extract`. The project is Apache-2.0 licensed. Read the actual [SKILL.md](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/SKILL.md) before adopting its defaults.

[`init`](https://impeccable.style/docs/init/) records audience, needs and constraints in `PRODUCT.md`; it does not select a palette. [`document`](https://impeccable.style/docs/document/) inspects code and, when available, the rendered interface, then writes Google-format `DESIGN.md` and generated `.impeccable/design.json` metadata. `document --seed` can establish a provisional direction before implementation. `extract` consolidates the implementation after patterns are understood. Review the output so a one-off accident does not become a permanent rule.

The narrower [interface-design skill](https://github.com/dammyjay93/interface-design/blob/main/.claude/skills/interface-design/SKILL.md) saves choices in `.interface-design/system.md` and reloads them across sessions. Its [repository](https://github.com/Dammyjay93/interface-design) documents Claude Code and Codex usage, and its [license is MIT](https://github.com/Dammyjay93/interface-design/blob/main/LICENSE). It is a reasonable alternative for application interfaces. Our preference is to choose one system record and workflow, avoiding competing documents with different token values.

### UI UX Pro Max

[UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) combines searchable design catalogs, Python scripts and stack-specific guidance. Its generator can persist a project `MASTER.md` with page overrides. The inspected repository supports multiple agents and includes `html-tailwind` guidance; it is MIT licensed. The [skill source template](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/src/ui-ux-pro-max/templates/base/skill-content.md) shows the actual procedure.

Our assessment is that this helps compare palettes, typography and interaction guidance. A generated recommendation is an input to design review, not evidence that a complete accessible component library exists. For Aweille, keep the chosen guidance and discard irrelevant framework advice. Its larger catalog and override structure are more than we need for three pages.

## Documents and executable tokens

### Google DESIGN.md, with optional Stitch extraction

Google's [DESIGN.md project](https://github.com/google-labs-code/design.md) specifies machine-readable YAML tokens alongside Markdown rationale. Its CLI can lint, diff and export tokens to DTCG or Tailwind formats. It is Apache-2.0 licensed and explicitly alpha, so schema changes remain a maintenance consideration. An ordinary file named `DESIGN.md` does not automatically follow this schema. Nor is its YAML schema identical to DTCG JSON.

This gives us a concrete, portable document for agent context. Our assessment is that its linter checks the record, including supported contrast pairs; it cannot establish accessibility or consistency of the rendered application.

Google Labs also supplies [`extract-design-md`](https://github.com/google-labs-code/stitch-skills/blob/main/plugins/stitch-design/skills/extract-design-md/SKILL.md), which reads source including plain HTML/CSS and writes `.stitch/DESIGN.md` without requiring a running app. The separate [`design-md`](https://github.com/google-labs-code/stitch-skills/blob/main/plugins/stitch-utilities/skills/design-md/README.md) workflow retrieves Stitch screens through MCP. [`manage-design-system`](https://github.com/google-labs-code/stitch-skills/blob/main/plugins/stitch-design/skills/manage-design-system/SKILL.md) uploads and applies systems inside Stitch. These are different workflows; local extraction need not commit us to the hosted service. The [skills are Apache-2.0 licensed](https://github.com/google-labs-code/stitch-skills/blob/main/LICENSE).

### CSS variables first, DTCG when exchange is needed

[CSS custom properties](https://www.w3.org/TR/css-variables-1/) provide named values with cascade and inheritance. Aweille already uses them. Our proposal is to extend its semantic tokens for text, surfaces, actions, borders, spacing and typography, then reference them in shared rules.

The [DTCG 2025.10 format](https://www.designtokens.org/tr/2025.10/format/) specifies typed token interchange, groups and aliases. It is a stable Community Group report, explicitly not a W3C Standard. Use it when exchanging tokens across tools or producing several platform outputs.

[Style Dictionary supports DTCG tokens](https://styledictionary.com/info/dtcg/) and can generate [CSS variables and other formats](https://styledictionary.com/reference/hooks/formats/predefined/). Our recommendation is to add that build step only when repeated conversion justifies it. Decide which file owns token values; manually editing CSS, YAML and JSON as independent authorities will create drift.

## Connecting agents to actual components and designs

### Storybook MCP

[Storybook's AI integration](https://storybook.js.org/docs/ai) is in preview. Its MCP server exposes component documentation, story generation and tests from a running Storybook. [Framework support](https://storybook.js.org/docs/ai/mcp/overview#framework-support) is more specific than saying it is React-only: development/testing tools work across Storybook projects; component manifests currently support React frameworks, Angular Vite and Vue 3 Vite, with an extra experimental docgen setting for Vue.

For Aweille, our assessment is to start with a small rendered reference page showing real Jinja/CSS patterns. Storybook would require another development toolchain and maintained stories, while its component API documentation does not directly understand Jinja macros. Reconsider it if we build a substantial reusable component library. Connecting an agent to documented examples is valuable; adopting Storybook is one way to do that.

### Figma MCP and Code Connect

[Figma MCP](https://developers.figma.com/docs/figma-mcp-server/) supplies design context and can write native canvas content. [Code Connect](https://developers.figma.com/docs/code-connect/) maps Figma components to actual production snippets, helping agents reuse the intended implementation. Its current [template files](https://developers.figma.com/docs/code-connect/template-files/) are framework agnostic; older framework parsers no longer receive support. Jinja/HTML mappings would still need authoring and maintenance.

Code Connect requires a Dev or Full seat on Professional, Organization or Enterprise; Professional permits one active library and framework. Current [MCP read limits](https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/) include 20 calls per month for Starter/View/Collab access, 200 daily for Professional/Organization Full or Dev seats, and 600 for Enterprise Full or Dev seats, with per-minute limits too. Some generative actions use separate AI credits. Canvas writing is documented as free during beta, with future usage-based pricing.

Our judgment is to choose Figma when visual editing and review in Figma are desired. Maintaining both a design library and code library is extra work for this app; MCP alone does not keep them synchronized.

### shadcn MCP and registries

[shadcn MCP](https://ui.shadcn.com/docs/mcp) lets agents browse, search and install code from public, private or third-party registries. [shadcn/ui](https://ui.shadcn.com/docs) distributes editable component source and provides a foundation for a custom design system. This is useful when intentionally adopting its component stack.

Our assessment is that installing its default components would pull Aweille toward a different frontend stack. A custom registry might distribute our own patterns later, but maintaining one now adds work without solving an observed problem. Use the registry concept as a future distribution option, not a reason to rewrite the UI.

## A minimal workflow to try

This is our proposed next experiment, not work performed during this research.

1. Audit the existing three screens and record product constraints, including phone use, forms, keyboard access and functional copy.
2. Choose a new direction using Arnaud's references and the product's workflows. The current appearance is an anti-reference. With Impeccable, the redesign flow establishes replacement visual decisions before documenting them.
3. Review one `DESIGN.md` containing exact tokens, rationale, component states and usage examples. Link it from agent instructions so later UI work reads it first.
4. Implement approved values through shared CSS and reusable Jinja patterns where repetition warrants them. Add a small reference page using the actual implementation.
5. For each change, have the agent reuse documented patterns, inspect screenshots on phone and desktop, exercise keyboard/error/empty states, and update code and documentation together.

The first trial should cover the weekly view and run form. Judge whether a later agent session can extend them consistently. Choose one primary skill; add Figma, a token compiler or Storybook only when that trial reveals a concrete missing capability. No reviewed skill removes the need for human design choices or browser verification.
