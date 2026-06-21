# Real Everlog Setup

The real integration path is export-folder based:

```text
Everlog export or scheduled backup
        -> local JSON/ZIP/Markdown/TXT folder
        -> everlog-memory-mcp scan/watch
        -> MCP tools for agents
```

This project does not need your Everlog passcode or Touch ID. You unlock Everlog
as usual when writing. Everlog writes backups to the folder you choose. This
project reads that folder.

## 1. Choose a stable export inbox

Recommended:

```text
/Volumes/EverlogVault/Everlog Exports
```

or another encrypted APFS volume / encrypted disk image.

For a quick local test, a normal folder works:

```text
~/Documents/Everlog Exports
```

Avoid putting real diary exports inside the Git repo.

Everlog manual exports may create timestamped names such as:

```text
Everlog Export YYYY-MM-DD_HH-MM-SS
```

Do not point the project at only one timestamped folder if you plan to export
again. Put each export folder or zip into the stable inbox and point the project
at the inbox. Entry ids are based on Everlog entry identifiers, so repeated
exports update the same entries instead of duplicating them.

## 2. Configure Everlog

If scheduled automatic backups are available, point the backup/export destination
at the folder from step 1. If not, manually export and move the resulting zip or
extracted folder into the stable inbox.

This is the only place where Everlog needs your normal unlock flow. The MCP
server never receives the password and does not call Touch ID.

## 3. Point this project at that folder

From the project directory:

```bash
cd /path/to/everlog-memory-mcp

python3 -m everlog_memory_mcp configure-source \
  "$HOME/Documents/Everlog Exports" \
  --config config.json \
  --source-mode everlog \
  --no-store-plaintext-index \
  --scan
```

Replace the folder path with the actual Everlog backup folder.

If you want to point at a single extracted export for testing:

```bash
python3 -m everlog_memory_mcp configure-source \
  "$HOME/Documents/Everlog Exports/Everlog Export YYYY-MM-DD_HH-MM-SS" \
  --config config.json \
  --source-mode everlog \
  --no-store-plaintext-index \
  --scan
```

## 4. Keep it updated

Manual scan:

```bash
python3 -m everlog_memory_mcp scan --config config.json
```

Foreground watcher:

```bash
python3 -m everlog_memory_mcp watch --config config.json --interval 30
```

Background watcher with launchd:

```bash
python3 -m everlog_memory_mcp install-launch-agent --config config.json --interval 30
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/io.github.visionary5.everlog-memory.watch.plist
```

Stop it:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/io.github.visionary5.everlog-memory.watch.plist
```

Logs:

```text
/path/to/everlog-memory-mcp/logs/watch.out.log
/path/to/everlog-memory-mcp/logs/watch.err.log
```

## One-time authorization model

There are two separate permissions:

- Everlog needs permission to write automatic backups to your chosen folder.
- The process that runs this MCP server needs permission to read that folder.

If the folder is in a normal location under your home directory, this often just
works. If the folder is under Desktop, Documents, Downloads, iCloud Drive, or an
external/encrypted volume, macOS may ask once for file access. If your MCP client
launches the server, the client app may need Files & Folders or Full Disk Access.

No repeated Everlog password is required because this project reads the exported
files, not Everlog's locked app database.
