from __future__ import annotations

import os
import plistlib
from pathlib import Path


DEFAULT_LABEL = "io.github.visionary5.everlog-memory.watch"


def write_launch_agent(
    python_path: Path,
    config_path: Path,
    project_dir: Path,
    interval_seconds: int = 30,
    label: str = DEFAULT_LABEL,
) -> Path:
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    logs_dir = project_dir / "logs"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    plist_path = launch_agents_dir / f"{label}.plist"
    payload = {
        "Label": label,
        "ProgramArguments": [
            str(python_path),
            "-m",
            "everlog_memory_mcp",
            "watch",
            "--config",
            str(config_path),
            "--interval",
            str(max(5, interval_seconds)),
        ],
        "WorkingDirectory": str(project_dir),
        "RunAtLoad": True,
        "KeepAlive": False,
        "StandardOutPath": str(logs_dir / "watch.out.log"),
        "StandardErrorPath": str(logs_dir / "watch.err.log"),
        "EnvironmentVariables": {
            "PYTHONUNBUFFERED": "1",
            "PATH": os.environ.get("PATH", ""),
        },
    }
    with plist_path.open("wb") as file:
        plistlib.dump(payload, file)
    plist_path.chmod(0o600)
    return plist_path
