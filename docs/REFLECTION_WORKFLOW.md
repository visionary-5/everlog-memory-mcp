# Reflection Workflow

The useful product is not a diary browser. The useful product is an artifact
loop:

```text
Everlog entries
        -> MCP evidence tools
        -> Codex / Claude reflection
        -> save_artifact
        -> structured local artifact store
        -> private web UI for review, comparison, and follow-up
```

## Why this matters

The browser UI should not try to replace a strong model with term counts. Top
terms and raw excerpts are low-value. Codex and Claude are the reflection engine;
this project is the local evidence layer, structured artifact store, and private
web UI.

## Saved artifacts

Structured artifacts live in:

```text
/path/to/everlog-memory-mcp/data/artifacts.sqlite3
```

Legacy Markdown reflections live under:

```text
/path/to/everlog-memory-mcp/data/reflections
```

This directory is ignored by Git. It can contain private agent-generated reports
such as:

- thinking-evolution reports
- weekly/monthly period portraits
- theme maps
- blog/product idea maps
- private/public boundary reviews

## CLI save

Save an agent output manually:

```bash
pbpaste | python -m everlog_memory_mcp save-reflection \
  --config config.json \
  --title "2026-01-01 to 2026-01-14 thinking evolution" \
  --source codex \
  --date-range "2026-01-01..2026-01-14"
```

List saved reflections:

```bash
python -m everlog_memory_mcp list-reflections --config config.json
```

## MCP save

Codex or Claude should call `save_artifact` after generating a useful report.
The agent should ask before saving. `save_artifact` writes `model`, dimensions,
claims, evidence, questions, tags, and markdown body into the private local site
store. The private site renders `model` first. `body_markdown` is secondary.

Suggested prompt ending:

```text
如果你认为这份复盘值得沉淀，请先问我是否保存。得到确认后，调用
save_artifact，把报告保存为结构化本地 artifact。
```

## Good artifact structure

A strong saved reflection should contain:

- period/date range
- a `model` object with threads, moments, tensions, beliefs, seeds, decisions, questions
- four to seven reusable dimensions/lenses
- three to five claims
- evidence table with dates and entry ids
- interpretation separated from evidence
- next questions
- privacy/publication boundary

## Current UI shape

The web demo now treats artifacts as private-site records:

- `Growth Map`: latest self-model built from saved agent artifacts.
- `Threads`: long-running model objects.
- `Questions`: open loops and active decisions.
- `Seeds`: writing, product, research, or project ideas.
- `Library`: saved agent records.
- `Source Vault`: raw Everlog entries for checking only.

Older artifacts without `dimensions` still render: the UI maps claims into
temporary model objects. New agent outputs should write `model` directly.
