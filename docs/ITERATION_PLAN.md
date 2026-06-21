# Iteration Plan

The project has three separate problem tracks. Keeping them separate prevents
product ideas from leaking into the personal diary self-model.

## 1. Design Problems

Goal: make the private site feel like a thoughtful growth map, not a debug UI or
another diary reader.

Current decisions:

- `Growth Map` is the current self-model overview.
- `High-Signal Moments` preserves details the agent should not flatten.
- `Threads` is the second-level page for long-running lines of change.
- `Source Vault` is an evidence vault, not a primary reading surface.
- Entry ids should stay available to agents, but hidden from ordinary UI.

Next design work:

- Add object-level pages for threads, with history across artifacts.
- Add period comparison: what changed since the previous artifact.
- Add a more distinctive visual language for moments, tensions, and decisions.
- Add private/public review for writing seeds.

## 2. Engineering Problems

Goal: make updates fast, local-first, reproducible, and safe.

Current decisions:

- Everlog export is read-only evidence.
- The metadata index does not store diary bodies by default.
- MCP tools should retrieve bounded evidence instead of loading all entries.
- Artifacts are versioned snapshots; the latest artifact is the current model.

Next engineering work:

- Add automatic export folder watching for newly extracted Everlog exports.
- Add artifact diffing and object id stability across snapshots.
- Add stronger duplicate detection for threads and seeds.
- Add encrypted artifact storage.
- Add local embedding or hybrid retrieval so agents can find relevant older
  entries without full rereads.

## 3. Product Innovation Problems

Goal: make this more than "agent summarizes my diary."

Core bet:

> The useful product is an agent-maintained self-model with evidence, moments,
> tensions, decisions, and writing seeds. The diary is the source, not the
> interface.

Promising product loops:

- Moment capture: the agent surfaces specific details that felt important but
  would be lost in broad summaries.
- Longitudinal update: the agent updates existing threads instead of writing a
  new standalone summary every time.
- Decision memory: open loops carry forward until later evidence resolves or
  changes them.
- Private-to-public path: private reflections can become sanitized blog seeds.
- Model critique: the user can mark an agent object as wrong, too generic, too
  invasive, or genuinely useful.

What would make it feel "cool":

- A timeline of changes, not a wall of summaries.
- Small, sharp observations that feel like the agent actually read the diary.
- Visible evidence boundaries so trust is earned rather than assumed.
- A living map where old ideas move, merge, pause, or graduate into projects.

Near-term milestone:

Create a weekly update flow where another Codex or Claude can:

1. read the latest artifact,
2. read only new Everlog entries,
3. update existing model objects,
4. add 3-7 high-signal moments,
5. save one complete new artifact,
6. show a meaningful UI change without exposing raw diary text.
