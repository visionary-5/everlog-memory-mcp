from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .artifacts import ArtifactStore
from .config import Config
from .insights import build_dashboard, build_entries, build_entry, build_portrait, build_themes, local_answer
from .reflections import list_reflections, read_reflection


STATIC_DIR = Path(__file__).resolve().parents[1] / "web"


class DemoRequestHandler(BaseHTTPRequestHandler):
    config: Config

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        try:
            if path == "/":
                self.send_static("index.html", "text/html; charset=utf-8")
            elif path == "/app.js":
                self.send_static("app.js", "application/javascript; charset=utf-8")
            elif path == "/styles.css":
                self.send_static("styles.css", "text/css; charset=utf-8")
            elif path == "/api/dashboard":
                self.send_json(build_dashboard(self.config))
            elif path == "/api/entries":
                self.send_json({"entries": build_entries(self.config)})
            elif path == "/api/entry":
                entry_id = first(query, "id")
                if not entry_id:
                    self.send_error_json(HTTPStatus.BAD_REQUEST, "missing id")
                    return
                entry = build_entry(self.config, entry_id)
                if entry is None:
                    self.send_error_json(HTTPStatus.NOT_FOUND, "entry not found")
                    return
                self.send_json(entry)
            elif path == "/api/search":
                q = first(query, "q")
                if not q:
                    self.send_json({"query": "", "answer": "", "hits": []})
                    return
                self.send_json(local_answer(self.config, q))
            elif path == "/api/themes":
                self.send_json({"themes": build_themes(self.config)})
            elif path == "/api/portrait":
                self.send_json(build_portrait(self.config))
            elif path == "/api/reflections":
                self.send_json(
                    {
                        "reflections": [
                            {
                                "id": artifact.id,
                                "title": artifact.title,
                                "type": artifact.artifact_type,
                                "source": artifact.source,
                                "date_range": artifact.date_range,
                                "created_at": artifact.created_at,
                                "excerpt": artifact.excerpt,
                            }
                            for artifact in list_reflections(self.config)
                        ]
                    }
                )
            elif path == "/api/reflection":
                artifact_id = first(query, "id")
                if not artifact_id:
                    self.send_error_json(HTTPStatus.BAD_REQUEST, "missing id")
                    return
                body = read_reflection(self.config, artifact_id)
                if body is None:
                    self.send_error_json(HTTPStatus.NOT_FOUND, "reflection not found")
                    return
                self.send_json({"id": artifact_id, "body": body})
            elif path == "/api/artifacts":
                with ArtifactStore.open(self.config) as store:
                    self.send_json({"artifacts": store.list(), "timeline": store.timeline()})
            elif path == "/api/artifact":
                artifact_id = first(query, "id")
                if not artifact_id:
                    self.send_error_json(HTTPStatus.BAD_REQUEST, "missing id")
                    return
                with ArtifactStore.open(self.config) as store:
                    artifact = store.get(artifact_id)
                if artifact is None:
                    self.send_error_json(HTTPStatus.NOT_FOUND, "artifact not found")
                    return
                self.send_json(artifact)
            else:
                self.send_error_json(HTTPStatus.NOT_FOUND, "not found")
        except Exception as exc:  # noqa: BLE001 - demo should return visible errors.
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def log_message(self, format: str, *args: object) -> None:
        print(f"[demo] {self.address_string()} - {format % args}")

    def send_static(self, name: str, content_type: str) -> None:
        path = STATIC_DIR / name
        if not path.exists():
            self.send_error_json(HTTPStatus.NOT_FOUND, "static file not found")
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        body = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    value = values[0].strip()
    return value or None


def serve_demo(config: Config, host: str = "127.0.0.1", port: int = 8765) -> int:
    handler = type("ConfiguredDemoRequestHandler", (DemoRequestHandler,), {"config": config})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Everlog memory demo running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 130
    finally:
        server.server_close()
    return 0
