from __future__ import annotations

import json
from pathlib import Path


def render_client_config(client: str, project_dir: Path, config_path: Path) -> str:
    python_path = project_dir / ".conda" / "bin" / "python"
    if client == "codex":
        return render_codex_toml(python_path, project_dir, config_path)
    if client in {"claude", "claude-desktop"}:
        return render_claude_json(python_path, project_dir, config_path)
    if client == "generic-json":
        return render_generic_json(python_path, config_path)
    raise ValueError(f"unknown client: {client}")


def render_codex_toml(python_path: Path, project_dir: Path, config_path: Path) -> str:
    return f"""[mcp_servers.everlog_memory]
command = "{python_path}"
args = ["-m", "everlog_memory_mcp", "mcp", "--config", "{config_path}"]
cwd = "{project_dir}"
startup_timeout_sec = 10
tool_timeout_sec = 60
default_tools_approval_mode = "prompt"
"""


def render_claude_json(python_path: Path, project_dir: Path, config_path: Path) -> str:
    payload = {
        "mcpServers": {
            "everlog-memory": {
                "command": str(python_path),
                "args": [
                    "-m",
                    "everlog_memory_mcp",
                    "mcp",
                    "--config",
                    str(config_path),
                ],
                "cwd": str(project_dir),
            }
        }
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def render_generic_json(python_path: Path, config_path: Path) -> str:
    payload = {
        "name": "everlog-memory",
        "transport": "stdio",
        "command": str(python_path),
        "args": [
            "-m",
            "everlog_memory_mcp",
            "mcp",
            "--config",
            str(config_path),
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

