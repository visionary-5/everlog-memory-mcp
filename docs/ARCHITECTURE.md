# Product Architecture

Working product definition:

> A local-first personal reflection layer over Everlog exports.

Everlog remains the system of record for writing, passcode protection, iCloud
sync, and device-to-device continuity. This project only reads official
exports/backups and exposes a controlled interpretation layer to agents.

## Current ingestion model

```text
Everlog manual export or scheduled backup
        -> zip or extracted folder containing Entries.json
        -> stable export inbox
        -> local metadata index
        -> MCP tools
```

Example stable inbox:

```text
~/Documents/Everlog Exports
```

An Everlog export can contain long-form entries, metadata, and media attachment
references. The indexer should treat the export folder as evidence, not as a
place to write derived content.

## Local space

Local storage is unavoidable because the agent needs a readable source. The
product decision is to avoid multiplying large plaintext copies.

Current default:

- Keep Everlog export files in one stable inbox.
- Store only metadata in SQLite by default.
- Do not persist entry bodies while `store_plaintext_index: false`.
- Re-read the relevant entry from `Entries.json` only when a tool needs it.

Expected growth points:

- Media attachments.
- Keeping many timestamped full exports.
- Future derived artifacts, such as monthly portraits.

Needed later:

- Export retention policy: keep latest N exports, archive older exports, or
  keep only the latest full export when automatic backup is reliable.
- Optional encrypted artifact store for generated portraits and summaries.

## Security and privacy

There are three separate data layers:

```text
Everlog private app data
Everlog exported JSON/ZIP files
everlog-memory generated index and artifacts
```

This project deliberately does not bypass Everlog's app lock or read its private
database. The security problem moves to exported files: if the export inbox is a
normal folder, someone with filesystem access can read `Entries.json`.

Current protections:

- No generic filesystem MCP tool.
- Source mode `everlog` only reads Everlog `Entries.json` and zip exports.
- SQLite database permissions are owner-only when possible.
- Diary bodies are not stored in SQLite by default.
- Tool results are bounded by limits.

Remaining risk:

- The export JSON itself is plaintext on disk.
- Cloud agents can receive snippets returned by MCP tools.
- Repeated exports may leave old plaintext copies behind.

Recommended stronger setup:

- Put the export inbox in an encrypted APFS volume or encrypted sparse disk image.
- If iCloud Drive is used, enable Apple's Advanced Data Protection.
- Use local models for high-private sessions.
- Add an audit log before exposing this to more clients.

## Automation

Best automation path:

```text
Everlog scheduled backup
        -> stable iCloud Drive or local inbox
        -> watch command or LaunchAgent
        -> refreshed index
```

Current manual path:

1. Export from Everlog.
2. Put the zip or extracted export folder in the stable inbox.
3. Run `scan`, or keep `watch` running.

The project already supports both extracted folders and zip archives, so manual
unzip is not required anymore.

Hard boundary:

- If Everlog only exposes manual export, this project cannot make export fully
  automatic without UI automation or Everlog adding a better integration point.
- UI automation can be a personal workaround, but it is fragile and should not be
  the core product promise.

## Agent memory model

Do not treat memory as a loose vector dump. Use layered memory:

```text
Entry
  raw dated diary entry from Everlog export

Evidence
  bounded quote/excerpt with entry id and date

Theme thread
  recurring topic with dated evidence

Period portrait
  weekly/monthly/quarterly observations with evidence

Long portrait
  slow-changing claims, confidence, and supporting entries
```

The agent should remember observations, not rewrite the user's identity. A good
claim has:

- `claim`
- `theme`
- `evidence`
- `date_range`
- `confidence`
- `created_at`
- `last_reviewed_at`

## Final product shape

The likely end product is a local macOS app plus MCP server:

```text
Menu bar / desktop app
  - Sync status
  - Privacy status
  - Export inbox management
  - Background watcher

Reflection UI
  - Ask My Diary
  - Theme Threads
  - Period Portraits
  - Blog Seeds
  - Saved Reflection Artifacts
  - Privacy Console

MCP server
  - Claude, Codex, and other MCP clients
  - Local model clients that support MCP
```

Ollama or LM Studio alone are model servers, not full MCP clients. They can be
used when a client or agent runner connects both the local model and this MCP
server.

## Current correction

The first browser demo intentionally proved ingestion and display, but the raw
timeline/top-term experience is not the product. The product should center on
agent-generated artifacts:

```text
Codex/Claude reads evidence through MCP
        -> produces a high-quality reflection
        -> asks to save
        -> save_reflection writes a local private Markdown artifact
        -> UI presents the artifact and tracks follow-up questions
```
