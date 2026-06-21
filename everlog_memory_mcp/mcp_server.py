from __future__ import annotations

import json
import sys
from typing import Any

from .config import Config
from .tools import call_tool, tool_definitions

PROTOCOL_VERSION = "2025-06-18"
SERVER_INSTRUCTIONS = (
    "Use this server as a local Everlog diary evidence layer, not as a generic file browser. "
    "Prefer search_entries, trace_theme, summarize_period_context, and compare_periods before "
    "get_entry. Cite dates and entry ids. Keep diary quotations short. Separate observation from "
    "interpretation, avoid diagnosis or fixed identity labels, and ask before retrieving many full "
    "entries. For personal growth analysis, build theme timelines and period comparisons from "
    "evidence instead of summarizing raw diary text. Avoid top-term-only analysis. Preserve "
    "important tensions instead of compressing them into generic advice. After producing a "
    "useful report, ask the user whether to save it with save_artifact. The primary output "
    "should be a model object with threads, moments, tensions, beliefs, seeds, decisions, and questions; "
    "moments capture specific high-signal details that should not be flattened into macro themes. "
    "Claims, dimensions, evidence, tags, and markdown body are supporting structure. For daily "
    "or weekly growth-map artifacts, read new entries first, compare against saved artifacts, "
    "update long-running objects, and only retrieve full old entries when evidence must be "
    "checked. Treat the latest artifact as the working self-model; produce a complete updated "
    "snapshot, not a delta list, and do not duplicate the same thread under a new title. Every "
    "model object must label its basis as diary_evidence, prior_artifact, "
    "conversation_context, agent_hypothesis, or mixed. Do not present current chat context or "
    "product planning as diary-derived insight; use conversation_context or mixed with a "
    "basis_note. For thinking_evolution and period_portrait artifacts, model.seeds should be "
    "diary-grounded; repo or product planning belongs in a separate product_idea artifact or "
    "project docs. The UI should not become a diary mirror, so avoid long diary excerpts."
)


class McpServer:
    def __init__(self, config: Config):
        self.config = config

    def serve(self) -> int:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle(request)
            except Exception as exc:  # noqa: BLE001 - must return JSON-RPC errors.
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(exc)},
                }
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        return 0

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params") or {}

        if method == "notifications/initialized":
            return None
        if method == "initialize":
            return result(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "everlog-memory-mcp", "version": "0.1.0"},
                    "instructions": SERVER_INSTRUCTIONS,
                },
            )
        if method == "tools/list":
            return result(request_id, {"tools": tool_definitions()})
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if not isinstance(name, str):
                return error(request_id, -32602, "tools/call requires a tool name")
            try:
                text = call_tool(self.config, name, arguments)
                return result(request_id, {"content": [{"type": "text", "text": text}]})
            except Exception as exc:  # noqa: BLE001 - surface tool failure to client.
                return error(request_id, -32000, str(exc))

        return error(request_id, -32601, f"method not found: {method}")


def result(request_id: Any, payload: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": payload}


def error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def serve(config: Config) -> int:
    return McpServer(config).serve()
