# Product Direction

This project should become a private growth map, not a diary clone.

The raw Everlog export is the evidence layer. Codex, Claude, or another strong
model maintains a longitudinal self-model. The web UI is the private site where
threads, moments, tensions, beliefs, seeds, decisions, and questions become durable
records that can be reviewed, compared, and extended.

## Design References

- Quartz: digital-garden patterns such as graph view, backlinks, tags, and
  search are useful for later cross-linking between ideas.
  <https://quartz.jzhao.xyz/>
- Astro content collections: a good future migration target if artifacts become
  file-backed Markdown/MDX with typed frontmatter.
  <https://docs.astro.build/en/guides/content-collections/>
- Docusaurus and Nextra: useful if this grows into a polished documentation or
  private blog shell, but they are less important than the artifact schema.
  <https://docusaurus.io/docs/blog>
  <https://nextra.site/docs>

## Core Loop

```text
Everlog export
        -> local MCP evidence tools
        -> strong agent updates model objects
        -> save_artifact
        -> structured private site
        -> next questions for future journals
```

## Product Principles

- Do not make the homepage a diary browser.
- Do not make top terms the main insight.
- Do not paste long diary bodies into generated artifacts.
- Preserve tension and uncertainty instead of compressing everything into a
  generic summary.
- Render model objects first: threads, moments, tensions, beliefs, seeds, decisions,
  questions. Claims and evidence support the model. Narrative body is secondary.
- Preserve high-signal details as moments so the agent cannot hide weak reading
  behind a smooth macro summary.
- Keep private data local by default; generated artifacts are also private local
  data unless explicitly exported.
- Read new diary entries first. Use old artifacts as memory. Re-open old diary
  entries only when checking evidence.

## Durable Objects

The agent should write objects that can survive across weeks and months:

- `threads`: long-running lines of thought, work, life, research, or identity.
- `moments`: specific scenes, reversals, or details with high feedback value.
- `tensions`: unresolved conflicts and tradeoffs.
- `beliefs`: judgments whose confidence or framing changed.
- `seeds`: writing, product, research, or project ideas.
- `decisions`: active path choices with options and current bias.
- `questions`: open loops for future journals.

## Next Product Steps

See [Iteration Plan](ITERATION_PLAN.md) for the current split between design,
engineering, and product-innovation work.

- Track the same model objects across multiple artifacts.
- Add an artifact comparison view: previous period vs current period.
- Add a private/public boundary review for blog candidates.
- Add graph links between artifacts, model objects, questions, and source entries.
- Add optional encrypted artifact storage before this contains months of real
  generated portraits.
