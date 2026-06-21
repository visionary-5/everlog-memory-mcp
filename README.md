# everlog-memory-mcp

[English](README.md) | [中文](README.zh-CN.md)

Unofficial local-first MCP server and private dashboard for structured
reflection over Everlog exports.

`everlog-memory-mcp` is not another diary app. Everlog remains the place where
writing happens. This project treats exported diary files as a local evidence
layer, lets agents query that evidence through MCP, and stores structured
agent-written artifacts as a private, versioned self-model.

> Status: early prototype / personal MVP. The core loop works, but the product,
> automation, encryption, and UI still need iteration.

## Why

LLM diary reflection often becomes either a raw summary or generic advice. This
project explores a different loop:

```text
Everlog export
  -> local metadata index
  -> MCP evidence tools
  -> agent updates structured self-model artifacts
  -> private growth-map UI
```

The goal is to preserve change over time: threads, high-signal moments,
tensions, belief shifts, decisions, questions, and writing or research seeds.

## Features

- Reads Everlog JSON exports, extracted `Entries.json` folders, zip exports,
  Markdown, and plain text diary exports.
- Builds a local SQLite metadata index.
- Defaults to `store_plaintext_index: false`, so diary bodies are not persisted
  into the metadata database.
- Exposes an MCP stdio server with bounded evidence tools.
- Saves structured agent artifacts into a local private artifact store.
- Provides a local web dashboard for Growth Map, Threads, High-Signal Moments,
  Open Loops, Seeds, Library, and Source Vault.

## Non-Goals

- It does not read Everlog's private app database.
- It does not bypass Everlog passcode, Touch ID, iCloud, or app sandboxing.
- It does not sync your diary to a hosted service.
- It does not call an LLM from the browser UI.
- It is not a security boundary against cloud model providers. If an agent sends
  diary excerpts to a cloud model, that provider can receive them.

## Privacy Model

The default mode is conservative:

- `config.json` is ignored by Git because it can contain private paths.
- `data/` is ignored by Git because it contains local indexes and artifacts.
- The metadata index stores ids, dates, paths, hashes, sizes, and mtimes.
- Diary bodies are read from export files on demand unless plaintext indexing is
  explicitly enabled.
- MCP tools return bounded excerpts and require the client or agent to call
  tools intentionally.

For stronger local privacy, keep Everlog exports and this project's `data/`
directory inside FileVault, an encrypted APFS volume, or an encrypted disk image.

## Installation

The project currently uses only the Python standard library.

```bash
git clone git@github.com:visionary-5/everlog-memory-mcp.git
cd everlog-memory-mcp
python3 -m everlog_memory_mcp --help
```

Create a local config file:

```bash
python3 -m everlog_memory_mcp init-config --path config.json
```

`config.json` is intentionally ignored by Git.

## Everlog JSON Export Workflow

Everlog manual exports may produce a zip file or an extracted folder with a name
like:

```text
Everlog Export YYYY-MM-DD_HH-MM-SS
```

Inside the export, this project looks for Everlog JSON data such as
`Entries.json`. It can read either:

- an extracted export folder containing `Entries.json`, or
- a zip file containing Everlog JSON.

Recommended setup:

1. Create a stable local inbox outside the Git repository:

   ```text
   ~/Documents/Everlog Exports
   ```

2. Put each new Everlog export zip or extracted export folder inside that inbox.

3. Point this project at the inbox, not at one timestamped export folder:

   ```bash
   python3 -m everlog_memory_mcp configure-source \
     "$HOME/Documents/Everlog Exports" \
     --config config.json \
     --source-mode everlog \
     --no-store-plaintext-index \
     --scan
   ```

Entry ids are based on Everlog entry identifiers, so repeated exports should
update the same entries instead of duplicating them.

For a one-off test, you can also point at a single extracted export folder:

```bash
python3 -m everlog_memory_mcp configure-source \
  "$HOME/Documents/Everlog Exports/Everlog Export YYYY-MM-DD_HH-MM-SS" \
  --config config.json \
  --source-mode everlog \
  --no-store-plaintext-index \
  --scan
```

## Updating the Index

Manual scan:

```bash
python3 -m everlog_memory_mcp scan --config config.json
```

Foreground watcher:

```bash
python3 -m everlog_memory_mcp watch --config config.json --interval 30
```

macOS LaunchAgent:

```bash
python3 -m everlog_memory_mcp install-launch-agent --config config.json --interval 30
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/io.github.visionary5.everlog-memory.watch.plist
```

Stop the LaunchAgent:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/io.github.visionary5.everlog-memory.watch.plist
```

## Local Web Dashboard

Run:

```bash
python3 -m everlog_memory_mcp demo --config config.json --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

The dashboard does not call an LLM. It renders the local index and saved
artifacts.

## MCP Setup

Run the MCP server over stdio:

```bash
python3 -m everlog_memory_mcp mcp --config config.json
```

Generate client config snippets:

```bash
python3 -m everlog_memory_mcp mcp-config --client codex --config config.json
python3 -m everlog_memory_mcp mcp-config --client claude-desktop --config config.json
python3 -m everlog_memory_mcp mcp-config --client generic-json --config config.json
```

Generic MCP config shape:

```json
{
  "mcpServers": {
    "everlog-memory": {
      "command": "python3",
      "args": [
        "-m",
        "everlog_memory_mcp",
        "mcp",
        "--config",
        "/absolute/path/to/everlog-memory-mcp/config.json"
      ],
      "cwd": "/absolute/path/to/everlog-memory-mcp"
    }
  }
}
```

## MCP Tools

Evidence tools:

- `privacy_status`
- `scan_exports`
- `search_entries`
- `get_entry`
- `summarize_period_context`
- `trace_theme`
- `compare_periods`

Artifact tools:

- `save_artifact`
- `list_artifacts`
- `read_artifact`
- `save_reflection`
- `list_reflections`
- `read_reflection`

Agents should cite dates and entry ids, keep direct quotations short, separate
evidence from interpretation, and update existing self-model objects instead of
creating duplicate summaries.

## Agent Artifact Workflow

The intended agent loop is:

1. Read the latest saved artifact with `list_artifacts` and `read_artifact`.
2. Run `scan_exports`.
3. Read only new or evidence-critical entries in full.
4. Update the existing self-model instead of appending another standalone
   summary.
5. Save one complete new artifact with `save_artifact`.

The model should contain:

- `threads`: long-running lines of thought, work, life, research, or identity.
- `moments`: concrete high-signal details that should not be flattened into a
  macro summary.
- `tensions`: recurring conflicts, tradeoffs, and unresolved contradictions.
- `beliefs`: judgments whose confidence or framing changed over time.
- `seeds`: diary-grounded writing, product, research, or project ideas.
- `decisions`: active path choices with options and current bias.
- `questions`: open loops for future journals.

Each object carries `basis` metadata such as `diary_evidence`,
`prior_artifact`, `conversation_context`, `agent_hypothesis`, or `mixed`, so the
UI can distinguish diary-grounded observations from hypotheses or project
planning.

See [Artifact Schema](docs/ARTIFACT_SCHEMA.md) and
[Agent Demo Prompts](docs/AGENT_DEMO.md).

## Current Product Shape

- `Growth Map`: current diary-grounded self-model overview.
- `High-Signal Moments`: concrete details the agent should not compress away.
- `Threads`: second-level view for long-running changes.
- `Open Loops`: decisions and questions to keep tracking.
- `Seeds`: diary-grounded ideas that may become writing, research, or projects.
- `Library`: versioned saved artifacts.
- `Source Vault`: raw diary entries for evidence checks only.

## Roadmap

Near-term:

- Better update protocol across multiple artifacts.
- Stable object ids and artifact diffing.
- Duplicate detection for recurring threads and seeds.
- More reliable automatic export-folder watching for repeated Everlog exports.
- Encrypted artifact storage.
- Local or hybrid retrieval so agents do not reread old entries unnecessarily.
- More polished private web UI and object-level history pages.

See [Iteration Plan](docs/ITERATION_PLAN.md) for the current split between
design, engineering, and product-innovation work.

## Documentation

- [Everlog integration](docs/EVERLOG.md)
- [Real Everlog setup](docs/REAL_EVERLOG_SETUP.md)
- [Product architecture](docs/ARCHITECTURE.md)
- [Local memory system](docs/MEMORY_SYSTEM.md)
- [Artifact schema](docs/ARTIFACT_SCHEMA.md)
- [Agent demo prompts](docs/AGENT_DEMO.md)
- [Iteration plan](docs/ITERATION_PLAN.md)
- [Reflection workflow](docs/REFLECTION_WORKFLOW.md)
- [Security notes](docs/SECURITY.md)
- [MCP client setup](docs/MCP_CLIENTS.md)
- [Product direction](docs/PRODUCT_DIRECTION.md)

## License

MIT.
