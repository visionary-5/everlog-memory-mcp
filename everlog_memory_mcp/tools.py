from __future__ import annotations

import json
from datetime import date
from typing import Any

from .artifacts import ArtifactStore
from .config import Config
from .indexer import scan
from .reflections import list_reflections, read_reflection, save_reflection
from .search import compare_periods, entries_in_period, get_entry, search_entries
from .store import Store


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "privacy_status",
            "description": "Show local privacy posture and index status.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "search_entries",
            "description": "Search configured Everlog export entries and return cited excerpts.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
        {
            "name": "get_entry",
            "description": "Read one diary entry by id returned from another tool.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "entry_id": {"type": "string"},
                    "max_chars": {"type": "integer", "minimum": 200, "maximum": 20000},
                },
                "required": ["entry_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "summarize_period_context",
            "description": "Return bounded evidence context for an agent to summarize a period.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 30},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "trace_theme",
            "description": "Trace how a theme appears over time using dated excerpts.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "theme": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 30},
                },
                "required": ["theme"],
                "additionalProperties": False,
            },
        },
        {
            "name": "compare_periods",
            "description": "Compare two date ranges and optionally focus on a theme.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "a_start": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "a_end": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "b_start": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "b_end": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "theme": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "scan_exports",
            "description": "Refresh the local metadata index from configured export folders.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "save_reflection",
            "description": "Save an agent-generated reflection report into the private local artifact store.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "artifact_type": {"type": "string"},
                    "source": {"type": "string"},
                    "date_range": {"type": "string"},
                },
                "required": ["title", "body"],
                "additionalProperties": False,
            },
        },
        {
            "name": "list_reflections",
            "description": "List saved agent-generated reflection artifacts.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "read_reflection",
            "description": "Read a saved reflection artifact by id.",
            "inputSchema": {
                "type": "object",
                "properties": {"artifact_id": {"type": "string"}},
                "required": ["artifact_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "save_artifact",
            "description": "Save a structured private-site artifact with model objects, moments, dimensions, claims, evidence, questions, and markdown body.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "artifact_type": {"type": "string"},
                    "source": {"type": "string"},
                    "date_range": {"type": "string"},
                    "summary": {"type": "string"},
                    "body_markdown": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "model": {
                        "type": "object",
                        "description": "Agent-maintained longitudinal self-model. Rendered as the primary private-site surface. Each object should include basis and optional basis_note to distinguish diary evidence from prior artifacts, conversation context, and hypotheses.",
                        "properties": {
                            "threads": {"type": "array", "items": {"type": "object"}},
                            "moments": {"type": "array", "items": {"type": "object"}},
                            "tensions": {"type": "array", "items": {"type": "object"}},
                            "beliefs": {"type": "array", "items": {"type": "object"}},
                            "seeds": {"type": "array", "items": {"type": "object"}},
                            "decisions": {"type": "array", "items": {"type": "object"}},
                            "questions": {"type": "array", "items": {"type": "object"}},
                        },
                    },
                    "dimensions": {
                        "type": "array",
                        "description": "Reusable lenses for the private site, such as career, AI, life state, projects, relationships, or study path.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "state": {"type": "string"},
                                "trajectory": {"type": "string"},
                                "status": {"type": "string"},
                                "confidence": {"type": "string"},
                                "signals": {"type": "array", "items": {"type": "string"}},
                                "evidence": {"type": "array", "items": {"type": "object"}},
                                "questions": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "claim": {"type": "string"},
                                "interpretation": {"type": "string"},
                                "confidence": {"type": "string"},
                                "evidence": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "entry_id": {"type": "string"},
                                            "date": {"type": "string"},
                                            "snippet": {"type": "string"},
                                            "note": {"type": "string"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "evidence": {"type": "array", "items": {"type": "object"}},
                    "questions": {"type": "array", "items": {}},
                },
                "required": ["title"],
                "additionalProperties": False,
            },
        },
        {
            "name": "list_artifacts",
            "description": "List structured private-site artifacts.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "read_artifact",
            "description": "Read one structured private-site artifact by id.",
            "inputSchema": {
                "type": "object",
                "properties": {"artifact_id": {"type": "string"}},
                "required": ["artifact_id"],
                "additionalProperties": False,
            },
        },
    ]


def call_tool(config: Config, name: str, arguments: dict[str, Any] | None) -> str:
    args = arguments or {}
    if name == "privacy_status":
        return json.dumps(privacy_status(config), ensure_ascii=False, indent=2)
    if name == "scan_exports":
        result = scan(config)
        return json.dumps(result.__dict__, ensure_ascii=False, indent=2)
    if name == "save_reflection":
        artifact = save_reflection(
            config,
            title=str(args["title"]),
            body=str(args["body"]),
            artifact_type=str(args.get("artifact_type") or "period_reflection"),
            source=str(args.get("source") or "agent"),
            date_range=str(args.get("date_range") or ""),
        )
        return json.dumps(
            {
                "id": artifact.id,
                "title": artifact.title,
                "path": str(artifact.path),
                "message": "reflection saved locally; this path is ignored by git",
            },
            ensure_ascii=False,
            indent=2,
        )
    if name == "list_reflections":
        return json.dumps(
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
    if name == "read_reflection":
        body = read_reflection(config, str(args["artifact_id"]))
        if body is None:
            raise ValueError("reflection not found")
        return body
    if name == "save_artifact":
        with ArtifactStore.open(config) as store:
            artifact = store.save(args)
        return json.dumps(artifact, ensure_ascii=False, indent=2)
    if name == "list_artifacts":
        with ArtifactStore.open(config) as store:
            artifacts = store.list()
        return json.dumps(artifacts, ensure_ascii=False, indent=2)
    if name == "read_artifact":
        with ArtifactStore.open(config) as store:
            artifact = store.get(str(args["artifact_id"]))
        if artifact is None:
            raise ValueError("artifact not found")
        return json.dumps(artifact, ensure_ascii=False, indent=2)
    if name == "search_entries":
        return json.dumps(
            [
                {
                    "id": hit.entry.id,
                    "date": hit.entry.entry_date.isoformat(),
                    "title": hit.entry.title,
                    "tags": list(hit.entry.tags),
                    "score": hit.score,
                    "excerpt": hit.excerpt,
                }
                for hit in search_entries(
                    config,
                    query=str(args["query"]),
                    start_date=parse_optional_date(args.get("start_date")),
                    end_date=parse_optional_date(args.get("end_date")),
                    limit=safe_limit(args.get("limit"), config.max_results, 20),
                )
            ],
            ensure_ascii=False,
            indent=2,
        )
    if name == "get_entry":
        entry = get_entry(config, str(args["entry_id"]))
        if entry is None:
            raise ValueError("entry not found")
        max_chars = safe_limit(args.get("max_chars"), config.max_entry_chars, 20_000)
        return json.dumps(
            {
                "id": entry.id,
                "date": entry.entry_date.isoformat(),
                "title": entry.title,
                "tags": list(entry.tags),
                "body": entry.body[:max_chars],
            },
            ensure_ascii=False,
            indent=2,
        )
    if name == "summarize_period_context":
        entries = entries_in_period(
            config,
            parse_optional_date(args.get("start_date")),
            parse_optional_date(args.get("end_date")),
            limit=safe_limit(args.get("limit"), config.max_results, 30),
        )
        return json.dumps(
            {
                "instruction": (
                    "Use these dated entries as evidence. Make cautious observations, "
                    "cite dates, and separate evidence from interpretation."
                ),
                "entries": [
                    {
                        "id": entry.id,
                        "date": entry.entry_date.isoformat(),
                        "title": entry.title,
                        "tags": list(entry.tags),
                        "excerpt": entry.body[:700],
                    }
                    for entry in entries
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    if name == "trace_theme":
        hits = search_entries(
            config,
            query=str(args["theme"]),
            start_date=parse_optional_date(args.get("start_date")),
            end_date=parse_optional_date(args.get("end_date")),
            limit=safe_limit(args.get("limit"), config.max_results, 30),
        )
        hits.sort(key=lambda hit: hit.entry.entry_date)
        return json.dumps(
            {
                "theme": str(args["theme"]),
                "instruction": (
                    "Build a timeline from these excerpts. Avoid diagnosing the writer; "
                    "describe observed changes and cite dates."
                ),
                "timeline": [
                    {
                        "id": hit.entry.id,
                        "date": hit.entry.entry_date.isoformat(),
                        "title": hit.entry.title,
                        "excerpt": hit.excerpt,
                    }
                    for hit in hits
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    if name == "compare_periods":
        return json.dumps(
            compare_periods(
                config,
                (parse_optional_date(args.get("a_start")), parse_optional_date(args.get("a_end"))),
                (parse_optional_date(args.get("b_start")), parse_optional_date(args.get("b_end"))),
                theme=args.get("theme"),
                limit=safe_limit(args.get("limit"), config.max_results, 20),
            ),
            ensure_ascii=False,
            indent=2,
        )
    raise ValueError(f"unknown tool: {name}")


def privacy_status(config: Config) -> dict[str, Any]:
    with Store(config.database_path) as store:
        count = store.count_entries()
        permissions = store.database_permissions()
    return {
        "source_dirs": [str(path) for path in config.source_dirs],
        "database_path": str(config.database_path),
        "database_permissions": permissions,
        "entry_count": count,
        "source_mode": config.source_mode,
        "store_plaintext_index": config.store_plaintext_index,
        "body_persistence": (
            "disabled: diary bodies are read from export files on demand"
            if not config.store_plaintext_index
            else "enabled: diary bodies are stored in SQLite plaintext"
        ),
        "mcp_boundary": "no generic filesystem access; only configured journal tools",
    }


def parse_optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    return date.fromisoformat(str(value))


def safe_limit(value: Any, default: int, maximum: int) -> int:
    if value in (None, ""):
        return min(default, maximum)
    return max(1, min(int(value), maximum))
