# Local Memory System

This project is a local-first memory layer around Everlog exports. Everlog stays
the writing app. The agent reads evidence through MCP and writes structured
self-model artifacts.

## Layers

1. `Everlog export`
   The source of truth. The project treats exported JSON, Markdown, or text as
   read-only diary evidence.

2. `Metadata index`
   A local SQLite index stores entry ids, dates, paths, hashes, sizes, and
   mtimes. In the default mode it does not persist diary bodies.

3. `Evidence tools`
   MCP tools expose bounded retrieval: search, period context, theme tracing,
   comparisons, and single-entry reads. Agents should use these tools to gather
   evidence instead of loading every diary entry every time.

4. `Artifact store`
   Agent outputs are saved as structured snapshots: `model`, `dimensions`,
   `claims`, `evidence`, `questions`, and readable markdown. This is the local
   long-term memory, separate from raw diary content.

5. `Latest self-model`
   The web UI renders the latest artifact as the current self-model. Older
   artifacts remain in the library as history, but the main interface is not a
   simple append-only pile.

6. `Private web surface`
   The UI is a review surface for the self-model. It should not become another
   diary reader or a raw transcript of agent summaries.

## Update Protocol

Agent updates should be full model revisions:

1. Read the latest artifact.
2. Scan the export folder for new or changed entries.
3. Read new entries in full when needed.
4. Use older entries only for search, theme tracing, and evidence checks.
5. Reuse existing model objects when the same thread continues.
6. Preserve concrete high-signal details as `moments` before forcing them into
   broad themes.
7. Add new objects only when there is enough diary evidence.
8. Mark stale objects as `paused`, `resolved`, or `retired` instead of deleting
   the idea from history.
9. Save one complete latest artifact.

This means the Library is versioned history, while Growth Map, Threads, Seeds,
and Open Loops render the latest self-model.

## Object Basis

Every model object must identify its source basis:

- `diary_evidence`: grounded in dated Everlog evidence with entry ids.
- `prior_artifact`: derived from a previous saved artifact.
- `conversation_context`: comes from the current chat or project discussion.
- `agent_hypothesis`: an inference that still needs evidence.
- `mixed`: combines diary evidence with another source.

Diary self-model views should privilege `diary_evidence`. Product planning from
the current project belongs in repo docs or a separate `product_idea` artifact,
not in the personal diary Growth Map.

## Privacy Boundary

The privacy boundary is local-first, not magic:

- The export folder can contain plaintext after Everlog export.
- `data/` and `config.json` are ignored by Git.
- The metadata index defaults to no body persistence.
- The artifact store may contain agent-written interpretations and short
  snippets, so it should be treated as private.
- For stronger local privacy, keep exports and `data/` inside FileVault,
  encrypted APFS, or an encrypted disk image.

Future work can add encrypted artifact storage, local embeddings, and a cleaner
automatic export watcher. The current MVP deliberately keeps the retrieval path
simple and inspectable.
