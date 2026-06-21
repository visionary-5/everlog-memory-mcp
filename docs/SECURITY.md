# Security Notes

This project is designed around a narrow boundary: it reads only the export
folders you configure. It does not inspect Everlog's app container, CloudKit
state, iCloud internals, or private SQLite files.

## Threat model

Protected by default:

- The MCP server has no generic filesystem-read tool.
- Journal bodies are not persisted into SQLite while
  `store_plaintext_index: false`.
- The SQLite database and `data/` directory are created with owner-only
  permissions.
- MCP results are capped by tool-specific limits.

Not protected by default:

- Everlog export files are whatever Everlog writes. If the export folder is a
  normal folder, those JSON/Markdown/TXT files are plaintext on disk.
- Paths and dates are stored in SQLite.
- Any cloud agent can receive snippets returned by this MCP server.

Recommended private setup:

1. Create an encrypted APFS volume or encrypted sparse disk image.
2. Configure Everlog automatic backups into that encrypted location.
3. Put `data/index.sqlite3` inside the same encrypted location if path metadata
   is sensitive to you.
4. Use a local model for private reflection sessions.
5. If using a cloud model, ask the agent to show what it plans to send before it
   calls tools that return long excerpts.

## Plaintext index mode

`store_plaintext_index: true` is intentionally opt-in. It allows future full-text
indexing, but it means journal titles, tags, and bodies can be persisted into
SQLite. Do not enable it unless the database lives inside an encrypted volume and
you understand the tradeoff.

The current implementation does not bundle SQLCipher. A later version can add a
SQLCipher-backed store, but the default safe behavior should remain "do not
persist diary bodies."
