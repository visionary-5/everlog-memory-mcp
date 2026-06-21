# MCP Client Setup

Run the server over stdio:

```bash
python3 \
  -m everlog_memory_mcp \
  mcp \
  --config /absolute/path/to/everlog-memory-mcp/config.json
```

Generic MCP client configuration shape:

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

The exact config file location depends on the client, such as Claude Desktop,
Cursor, or other MCP-compatible tools.

Generate snippets from the project:

```bash
python -m everlog_memory_mcp mcp-config --client codex --config config.json
python -m everlog_memory_mcp mcp-config --client claude-desktop --config config.json
python -m everlog_memory_mcp mcp-config --client generic-json --config config.json
```

## Codex

Codex supports STDIO MCP servers in the CLI and IDE extension. Add this to
`~/.codex/config.toml`, or use a project-scoped `.codex/config.toml` in a trusted
project:

```toml
[mcp_servers.everlog_memory]
command = "python3"
args = ["-m", "everlog_memory_mcp", "mcp", "--config", "/absolute/path/to/everlog-memory-mcp/config.json"]
cwd = "/absolute/path/to/everlog-memory-mcp"
startup_timeout_sec = 10
tool_timeout_sec = 60
default_tools_approval_mode = "prompt"
```

`default_tools_approval_mode = "prompt"` is intentional for diary data. It keeps
tool use visible instead of silently letting every query read journal context.

For diary data, project-scoped config is often safer than global config.

## Claude Desktop

Claude Desktop uses an `mcpServers` JSON shape. The exact file location depends
on the installed Claude client and platform, but the server config is:

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

Prefer local/project config for diary data so the MCP server is available only
where you explicitly enable it.

## Local models

Ollama and LM Studio provide local model inference. They do not, by themselves,
make a full agent that can call MCP tools. To use this diary server with a local
model, run it through an MCP-capable client or agent runner that can connect to
both:

- the local model provider, and
- this `everlog-memory` STDIO MCP server.

If the MCP client is a macOS app and your Everlog export folder is protected by
macOS privacy controls, grant that client app access to the folder or Full Disk
Access once in System Settings.

## Tool behavior

The tools are evidence providers:

- `search_entries` finds dated excerpts.
- `get_entry` reads one entry by id.
- `summarize_period_context` returns bounded period context.
- `trace_theme` returns a timeline for a theme.
- `compare_periods` returns side-by-side period evidence.
- `save_reflection` stores a useful agent-generated report locally.
- `list_reflections` and `read_reflection` manage saved reports.
- `privacy_status` shows the current privacy posture.

Suggested agent rule:

> Use diary excerpts as evidence. Cite dates. Separate observation from
> interpretation. Do not diagnose or label the writer.
