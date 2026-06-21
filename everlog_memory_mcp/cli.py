from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .artifacts import ArtifactStore
from .config import Config, configure_source, write_example_config
from .client_config import render_client_config
from .demo_server import serve_demo
from .indexer import scan
from .launch_agent import DEFAULT_LABEL, write_launch_agent
from .mcp_server import serve
from .reflections import list_reflections, read_reflection, save_reflection
from .search import compare_periods, get_entry, search_entries
from .tools import privacy_status
from .watcher import watch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="everlog-memory")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    config_parent = argparse.ArgumentParser(add_help=False)
    config_parent.add_argument(
        "--config",
        default=argparse.SUPPRESS,
        help="Path to config JSON",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-config", help="Write a starter config")
    init_parser.add_argument("--path", default="config.json")

    configure_parser = subparsers.add_parser(
        "configure-source",
        parents=[config_parent],
        help="Point config at real Everlog export folders",
    )
    configure_parser.add_argument("source_dirs", nargs="+")
    configure_parser.add_argument("--database-path")
    configure_parser.add_argument("--create", action="store_true", help="Create missing source dirs")
    configure_parser.add_argument(
        "--source-mode",
        choices=("mixed", "everlog"),
        help="mixed reads Markdown/TXT plus Everlog exports; everlog reads only Entries.json/zip exports",
    )
    configure_parser.add_argument(
        "--store-plaintext-index",
        dest="store_plaintext_index",
        action="store_true",
        default=None,
        help="Persist diary bodies in SQLite plaintext",
    )
    configure_parser.add_argument(
        "--no-store-plaintext-index",
        dest="store_plaintext_index",
        action="store_false",
        help="Do not persist diary bodies in SQLite",
    )
    configure_parser.add_argument("--scan", action="store_true", help="Scan after writing config")

    subparsers.add_parser("scan", parents=[config_parent], help="Refresh the metadata index")
    subparsers.add_parser("status", parents=[config_parent], help="Show privacy and index status")

    watch_parser = subparsers.add_parser(
        "watch",
        parents=[config_parent],
        help="Continuously refresh the metadata index",
    )
    watch_parser.add_argument("--interval", type=int, default=30, help="Polling interval in seconds")

    search_parser = subparsers.add_parser("search", parents=[config_parent], help="Search entries")
    search_parser.add_argument("query")
    search_parser.add_argument("--start-date")
    search_parser.add_argument("--end-date")
    search_parser.add_argument("--limit", type=int)

    get_parser = subparsers.add_parser("get", parents=[config_parent], help="Read one entry by id")
    get_parser.add_argument("entry_id")
    get_parser.add_argument("--max-chars", type=int, default=4000)

    trace_parser = subparsers.add_parser("trace", parents=[config_parent], help="Trace a theme over time")
    trace_parser.add_argument("theme")
    trace_parser.add_argument("--start-date")
    trace_parser.add_argument("--end-date")
    trace_parser.add_argument("--limit", type=int)

    compare_parser = subparsers.add_parser(
        "compare",
        parents=[config_parent],
        help="Compare two periods",
    )
    compare_parser.add_argument("--a-start")
    compare_parser.add_argument("--a-end")
    compare_parser.add_argument("--b-start")
    compare_parser.add_argument("--b-end")
    compare_parser.add_argument("--theme")
    compare_parser.add_argument("--limit", type=int)

    launch_parser = subparsers.add_parser(
        "install-launch-agent",
        parents=[config_parent],
        help="Write a macOS LaunchAgent plist for background scanning",
    )
    launch_parser.add_argument("--interval", type=int, default=30)
    launch_parser.add_argument("--label", default=DEFAULT_LABEL)
    launch_parser.add_argument(
        "--python",
        default=str(Path(__file__).resolve().parents[1] / ".conda" / "bin" / "python"),
        help="Python executable for launchd",
    )

    mcp_config_parser = subparsers.add_parser(
        "mcp-config",
        parents=[config_parent],
        help="Print MCP client configuration snippets",
    )
    mcp_config_parser.add_argument(
        "--client",
        choices=("codex", "claude-desktop", "generic-json"),
        default="codex",
    )

    save_reflection_parser = subparsers.add_parser(
        "save-reflection",
        parents=[config_parent],
        help="Save an agent-generated reflection into the private local artifact store",
    )
    save_reflection_parser.add_argument("--title", required=True)
    save_reflection_parser.add_argument("--type", default="period_reflection")
    save_reflection_parser.add_argument("--source", default="agent")
    save_reflection_parser.add_argument("--date-range", default="")
    save_reflection_parser.add_argument(
        "--file",
        help="Markdown file to import. If omitted, read from stdin.",
    )

    subparsers.add_parser(
        "list-reflections",
        parents=[config_parent],
        help="List saved reflection artifacts",
    )

    read_reflection_parser = subparsers.add_parser(
        "read-reflection",
        parents=[config_parent],
        help="Read one saved reflection artifact",
    )
    read_reflection_parser.add_argument("artifact_id")

    save_artifact_parser = subparsers.add_parser(
        "save-artifact",
        parents=[config_parent],
        help="Save a structured JSON artifact into the private site store",
    )
    save_artifact_parser.add_argument(
        "--file",
        help="JSON file to import. If omitted, read JSON from stdin.",
    )

    subparsers.add_parser(
        "list-artifacts",
        parents=[config_parent],
        help="List structured private-site artifacts",
    )

    read_artifact_parser = subparsers.add_parser(
        "read-artifact",
        parents=[config_parent],
        help="Read one structured private-site artifact",
    )
    read_artifact_parser.add_argument("artifact_id")

    subparsers.add_parser("mcp", parents=[config_parent], help="Run the MCP stdio server")

    demo_parser = subparsers.add_parser(
        "demo",
        parents=[config_parent],
        help="Run the local web demo",
    )
    demo_parser.add_argument("--host", default="127.0.0.1")
    demo_parser.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)

    if args.command == "init-config":
        path = write_example_config(Path(args.path))
        print(f"Wrote {path}")
        return 0

    if args.command == "configure-source":
        config = configure_source(
            args.config,
            args.source_dirs,
            database_path=args.database_path,
            create_dirs=args.create,
            source_mode=args.source_mode,
            store_plaintext_index=args.store_plaintext_index,
        )
        print(json.dumps(config.to_dict(), ensure_ascii=False, indent=2))
        if args.scan:
            result = scan(config)
            print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0

    config = Config.from_file(args.config)

    if args.command == "scan":
        result = scan(config)
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0
    if args.command == "status":
        print(json.dumps(privacy_status(config), ensure_ascii=False, indent=2))
        return 0
    if args.command == "watch":
        def report(result):
            print(json.dumps(result.__dict__, ensure_ascii=False), flush=True)

        return watch(config, interval_seconds=args.interval, on_scan=report)
    if args.command == "search":
        hits = search_entries(
            config,
            args.query,
            start_date=parse_date_arg(args.start_date),
            end_date=parse_date_arg(args.end_date),
            limit=args.limit,
        )
        print(
            json.dumps(
                [
                    {
                        "id": hit.entry.id,
                        "date": hit.entry.entry_date.isoformat(),
                        "title": hit.entry.title,
                        "score": hit.score,
                        "excerpt": hit.excerpt,
                    }
                    for hit in hits
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "get":
        entry = get_entry(config, args.entry_id)
        if entry is None:
            print("entry not found")
            return 1
        print(
            json.dumps(
                {
                    "id": entry.id,
                    "date": entry.entry_date.isoformat(),
                    "title": entry.title,
                    "tags": list(entry.tags),
                    "body": entry.body[: args.max_chars],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "trace":
        hits = search_entries(
            config,
            args.theme,
            start_date=parse_date_arg(args.start_date),
            end_date=parse_date_arg(args.end_date),
            limit=args.limit,
        )
        hits.sort(key=lambda hit: hit.entry.entry_date)
        print(
            json.dumps(
                [
                    {
                        "id": hit.entry.id,
                        "date": hit.entry.entry_date.isoformat(),
                        "title": hit.entry.title,
                        "excerpt": hit.excerpt,
                    }
                    for hit in hits
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "compare":
        print(
            json.dumps(
                compare_periods(
                    config,
                    (parse_date_arg(args.a_start), parse_date_arg(args.a_end)),
                    (parse_date_arg(args.b_start), parse_date_arg(args.b_end)),
                    theme=args.theme,
                    limit=args.limit,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "install-launch-agent":
        plist_path = write_launch_agent(
            python_path=Path(args.python).expanduser().resolve(),
            config_path=Path(args.config).expanduser().resolve(),
            project_dir=Path(__file__).resolve().parents[1],
            interval_seconds=args.interval,
            label=args.label,
        )
        print(f"Wrote {plist_path}")
        print("Load it with:")
        print(f"launchctl bootstrap gui/$(id -u) {plist_path}")
        print("Stop it with:")
        print(f"launchctl bootout gui/$(id -u) {plist_path}")
        return 0
    if args.command == "mcp-config":
        project_dir = Path(__file__).resolve().parents[1]
        config_path = Path(args.config).expanduser().resolve()
        print(render_client_config(args.client, project_dir, config_path))
        return 0
    if args.command == "save-reflection":
        if args.file:
            body = Path(args.file).expanduser().read_text(encoding="utf-8")
        else:
            body = sys.stdin.read()
        artifact = save_reflection(
            config,
            title=args.title,
            body=body,
            artifact_type=args.type,
            source=args.source,
            date_range=args.date_range,
        )
        print(
            json.dumps(
                {
                    "id": artifact.id,
                    "title": artifact.title,
                    "path": str(artifact.path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "list-reflections":
        print(
            json.dumps(
                [
                    {
                        "id": artifact.id,
                        "title": artifact.title,
                        "type": artifact.artifact_type,
                        "source": artifact.source,
                        "date_range": artifact.date_range,
                        "created_at": artifact.created_at,
                        "excerpt": artifact.excerpt,
                    }
                    for artifact in list_reflections(config)
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "read-reflection":
        body = read_reflection(config, args.artifact_id)
        if body is None:
            print("reflection not found")
            return 1
        print(body)
        return 0
    if args.command == "save-artifact":
        raw = Path(args.file).expanduser().read_text(encoding="utf-8") if args.file else sys.stdin.read()
        payload = json.loads(raw)
        with ArtifactStore.open(config) as store:
            artifact = store.save(payload)
        print(json.dumps(artifact, ensure_ascii=False, indent=2))
        return 0
    if args.command == "list-artifacts":
        with ArtifactStore.open(config) as store:
            artifacts = store.list()
        print(json.dumps(artifacts, ensure_ascii=False, indent=2))
        return 0
    if args.command == "read-artifact":
        with ArtifactStore.open(config) as store:
            artifact = store.get(args.artifact_id)
        if artifact is None:
            print("artifact not found")
            return 1
        print(json.dumps(artifact, ensure_ascii=False, indent=2))
        return 0
    if args.command == "mcp":
        return serve(config)
    if args.command == "demo":
        return serve_demo(config, host=args.host, port=args.port)

    parser.error(f"unknown command: {args.command}")
    return 2


def parse_date_arg(value: str | None):
    if not value:
        return None
    from datetime import date

    return date.fromisoformat(value)
