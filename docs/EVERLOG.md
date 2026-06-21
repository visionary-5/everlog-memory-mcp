# Everlog Integration

Everlog is treated as the source of truth. This project reads exports/backups.

## What this project does not do

- It does not bypass Everlog's password, Touch ID, or Face ID protection.
- It does not read private app databases.
- It does not depend on Everlog internals.
- It does not require replacing Everlog as your writing app.

## Recommended export format

Use Everlog JSON when available. This project supports extracted `Entries.json`
folders and zip files containing Everlog JSON. Markdown and plain text are still
supported for simpler export workflows. Avoid PDF because it is harder to parse
accurately and often loses useful structure.

## Automatic updates

Configure Everlog scheduled automatic backups if available in your version, then
point `source_dirs` at that backup directory.

Run one scan manually:

```bash
python -m everlog_memory_mcp scan --config config.json
```

Run continuous polling:

```bash
python -m everlog_memory_mcp watch --config config.json --interval 30
```

The watcher is deliberately simple for the MVP. It rescans the configured export
folders and updates only changed files by hash/mtime. A macOS LaunchAgent can run
the watcher in the background later.

Configure the real source folder:

```bash
python -m everlog_memory_mcp configure-source \
  "/path/to/everlog/backups" \
  --config config.json \
  --source-mode everlog \
  --no-store-plaintext-index \
  --scan
```

Generate a user LaunchAgent for background scans:

```bash
python -m everlog_memory_mcp install-launch-agent --config config.json --interval 30
```

## Writing back to Everlog

Everlog's public URL Scheme can create entries. This project does not implement
write-back yet because opening app URLs from a background MCP server needs a
clear consent flow. A future tool could create a "weekly reflection" entry after
showing the content to the user first.
