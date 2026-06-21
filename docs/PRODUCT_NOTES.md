# Product Notes

Working framing:

> A local-first personal reflection layer over an existing diary.

The project is not trying to become another diary app. Everlog remains the place
where writing happens. This server adds a controlled interpretation layer that
different agents can use.

## MVP

1. Read Everlog Markdown/TXT automatic backups.
2. Maintain a local metadata index without persisting bodies by default.
3. Expose careful, citation-friendly MCP tools.
4. Support theme tracing and period comparison.

## Product principles

- The user owns the journal data.
- The agent should not define who the user is.
- Any portrait or interpretation should cite dates and excerpts.
- Local-first should be the default.
- Cloud-model use should be explicit and bounded.

## Later ideas

- SQLCipher store.
- macOS LaunchAgent installer for `watch`.
- Local model integration.
- Read-only web UI for timelines and period portraits.
- Consent-based Everlog write-back using URL Scheme.
- Import adapters for other journal export formats.

