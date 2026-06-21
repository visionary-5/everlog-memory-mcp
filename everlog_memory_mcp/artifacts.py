from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Config


SLUG_RE = re.compile(r"[^a-z0-9\u4e00-\u9fff]+")
ALLOWED_BASIS = {
    "diary_evidence",
    "prior_artifact",
    "conversation_context",
    "agent_hypothesis",
    "mixed",
}
BASIS_ALIASES = {
    "diary": "diary_evidence",
    "evidence": "diary_evidence",
    "artifact": "prior_artifact",
    "prior": "prior_artifact",
    "conversation": "conversation_context",
    "chat": "conversation_context",
    "hypothesis": "agent_hypothesis",
    "inference": "agent_hypothesis",
}


@dataclass(frozen=True)
class ArtifactStore:
    path: Path
    conn: sqlite3.Connection

    @classmethod
    def open(cls, config: Config) -> "ArtifactStore":
        path = config.database_path.parent / "artifacts.sqlite3"
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        store = cls(path=path, conn=conn)
        store.ensure_schema()
        try:
            path.chmod(0o600)
        except PermissionError:
            pass
        return store

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "ArtifactStore":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def ensure_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                source TEXT NOT NULL,
                date_range TEXT,
                summary TEXT,
                body_markdown TEXT NOT NULL,
                dimensions_json TEXT NOT NULL DEFAULT '[]',
                model_json TEXT NOT NULL DEFAULT '{}',
                tags_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY,
                artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
                claim TEXT NOT NULL,
                interpretation TEXT,
                confidence TEXT,
                sort_order INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
                claim_id TEXT REFERENCES claims(id) ON DELETE CASCADE,
                entry_id TEXT,
                entry_date TEXT,
                snippet TEXT,
                note TEXT
            );

            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
                question TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                note TEXT
            );
            """
        )
        columns = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(artifacts)").fetchall()
        }
        if "dimensions_json" not in columns:
            self.conn.execute(
                "ALTER TABLE artifacts ADD COLUMN dimensions_json TEXT NOT NULL DEFAULT '[]'"
            )
        if "model_json" not in columns:
            self.conn.execute(
                "ALTER TABLE artifacts ADD COLUMN model_json TEXT NOT NULL DEFAULT '{}'"
            )
        self.conn.commit()

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_artifact_payload(payload)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        artifact_id = normalized.get("id") or f"{now[:10]}-{slugify(normalized['title'])}"
        artifact_id = unique_artifact_id(self.conn, artifact_id)

        self.conn.execute(
            """
            INSERT INTO artifacts(
                id, title, artifact_type, source, date_range, summary,
                body_markdown, dimensions_json, model_json, tags_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                normalized["title"],
                normalized["artifact_type"],
                normalized["source"],
                normalized["date_range"],
                normalized["summary"],
                normalized["body_markdown"],
                json.dumps(normalized["dimensions"], ensure_ascii=False),
                json.dumps(normalized["model"], ensure_ascii=False),
                json.dumps(normalized["tags"], ensure_ascii=False),
                now,
                now,
            ),
        )

        for index, claim in enumerate(normalized["claims"]):
            claim_id = f"{artifact_id}-claim-{index + 1}"
            self.conn.execute(
                """
                INSERT INTO claims(id, artifact_id, claim, interpretation, confidence, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    artifact_id,
                    claim["claim"],
                    claim.get("interpretation", ""),
                    claim.get("confidence", ""),
                    index,
                ),
            )
            for item in claim.get("evidence", []):
                self.insert_evidence(artifact_id, claim_id, item)

        for item in normalized["evidence"]:
            self.insert_evidence(artifact_id, None, item)

        for item in normalized["questions"]:
            if isinstance(item, str):
                question = {"question": item}
            else:
                question = item
            self.conn.execute(
                """
                INSERT INTO questions(artifact_id, question, status, note)
                VALUES (?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    question.get("question", ""),
                    question.get("status", "open"),
                    question.get("note", ""),
                ),
            )

        self.conn.commit()
        return self.get(artifact_id) or {"id": artifact_id}

    def insert_evidence(self, artifact_id: str, claim_id: str | None, item: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO evidence(artifact_id, claim_id, entry_id, entry_date, snippet, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                claim_id,
                evidence_value(item, "entry_id", "entryId", "id"),
                evidence_value(item, "date", "entry_date", "entryDate"),
                evidence_value(item, "snippet", "excerpt", "quote", "text"),
                evidence_value(item, "note", "reason", "interpretation", "why"),
            ),
        )

    def list(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT
                artifacts.*,
                (SELECT COUNT(*) FROM claims WHERE artifact_id = artifacts.id) AS claim_count,
                (SELECT COUNT(*) FROM evidence WHERE artifact_id = artifacts.id) AS evidence_count,
                (SELECT COUNT(*) FROM questions WHERE artifact_id = artifacts.id) AS question_count
            FROM artifacts
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
        return [artifact_summary(row, include_body=False) for row in rows]

    def get(self, artifact_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
        if row is None:
            return None
        artifact = artifact_summary(row, include_body=True)
        claims = self.conn.execute(
            "SELECT * FROM claims WHERE artifact_id = ? ORDER BY sort_order ASC",
            (artifact_id,),
        ).fetchall()
        evidence = self.conn.execute(
            "SELECT * FROM evidence WHERE artifact_id = ? ORDER BY id ASC",
            (artifact_id,),
        ).fetchall()
        questions = self.conn.execute(
            "SELECT * FROM questions WHERE artifact_id = ? ORDER BY id ASC",
            (artifact_id,),
        ).fetchall()
        evidence_by_claim: dict[str, list[dict[str, Any]]] = {}
        loose_evidence: list[dict[str, Any]] = []
        for item in evidence:
            parsed = evidence_row(item)
            if item["claim_id"]:
                evidence_by_claim.setdefault(item["claim_id"], []).append(parsed)
            else:
                loose_evidence.append(parsed)
        artifact["claims"] = [
            {
                "id": claim["id"],
                "claim": claim["claim"],
                "interpretation": claim["interpretation"],
                "confidence": claim["confidence"],
                "evidence": evidence_by_claim.get(claim["id"], []),
            }
            for claim in claims
        ]
        artifact["evidence"] = loose_evidence
        artifact["questions"] = [
            {
                "id": item["id"],
                "question": item["question"],
                "status": item["status"],
                "note": item["note"],
            }
            for item in questions
        ]
        artifact["claim_count"] = len(artifact["claims"])
        artifact["evidence_count"] = len(evidence)
        artifact["question_count"] = len(artifact["questions"])
        return artifact

    def timeline(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT entry_date, entry_id, snippet, note, artifact_id
            FROM evidence
            WHERE entry_date IS NOT NULL AND entry_date != ''
            ORDER BY entry_date ASC, id ASC
            """
        ).fetchall()
        return [evidence_row(row) | {"artifact_id": row["artifact_id"]} for row in rows]


def normalize_artifact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(payload.get("id") or ""),
        "title": str(payload.get("title") or "Untitled reflection"),
        "artifact_type": str(payload.get("artifact_type") or payload.get("type") or "reflection"),
        "source": str(payload.get("source") or "agent"),
        "date_range": str(payload.get("date_range") or ""),
        "summary": str(payload.get("summary") or ""),
        "body_markdown": str(payload.get("body_markdown") or payload.get("body") or ""),
        "dimensions": normalize_dimensions(payload.get("dimensions") or payload.get("lenses") or []),
        "model": normalize_model(payload.get("model") or {}),
        "tags": list_of_strings(payload.get("tags") or []),
        "claims": list_of_dicts(payload.get("claims") or []),
        "evidence": list_of_dicts(payload.get("evidence") or []),
        "questions": list(payload.get("questions") or []),
    }


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def normalize_model(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "threads": normalize_model_items(value.get("threads"), "thread"),
        "moments": normalize_model_items(value.get("moments"), "moment"),
        "tensions": normalize_model_items(value.get("tensions"), "tension"),
        "beliefs": normalize_model_items(value.get("beliefs"), "belief"),
        "seeds": normalize_model_items(value.get("seeds"), "seed"),
        "decisions": normalize_model_items(value.get("decisions"), "decision"),
        "questions": normalize_model_items(value.get("questions"), "question"),
    }


def normalize_model_items(value: Any, kind: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in list_of_dicts(value):
        normalized = {
            "kind": str(item.get("kind") or kind),
            "title": str(item.get("title") or item.get("name") or item.get("question") or ""),
            "summary": str(item.get("summary") or item.get("state") or item.get("current_read") or ""),
            "movement": str(
                item.get("movement")
                or item.get("trajectory")
                or item.get("change")
                or item.get("direction")
                or ""
            ),
            "why_it_matters": str(item.get("why_it_matters") or item.get("why") or ""),
            "feedback": str(item.get("feedback") or item.get("response") or ""),
            "status": str(item.get("status") or item.get("phase") or ""),
            "confidence": str(item.get("confidence") or ""),
            "basis": normalize_basis(item.get("basis") or item.get("source_basis"), item),
            "basis_note": str(item.get("basis_note") or item.get("source_note") or ""),
            "private_public": str(
                item.get("private_public")
                or item.get("privacy")
                or item.get("boundary")
                or item.get("visibility")
                or ""
            ),
            "next_step": str(item.get("next_step") or item.get("next_action") or ""),
            "signals": list_of_strings(item.get("signals") or item.get("markers") or []),
            "evidence": [normalize_evidence_item(e) for e in list_of_dicts(item.get("evidence") or [])],
        }
        if normalized["basis"] == "agent_hypothesis" and normalized["confidence"] in {
            "medium-high",
            "high",
        }:
            normalized["confidence"] = "medium"
        if normalized["title"] or normalized["summary"] or normalized["movement"]:
            items.append(normalized)
    return items


def infer_basis(item: dict[str, Any]) -> str:
    if has_diary_evidence(item):
        return "diary_evidence"
    return "agent_hypothesis"


def normalize_basis(value: Any, item: dict[str, Any]) -> str:
    raw = str(value or "").strip()
    if raw:
        basis = BASIS_ALIASES.get(raw, raw)
        if basis in ALLOWED_BASIS:
            if basis == "diary_evidence" and not has_diary_evidence(item):
                return "agent_hypothesis"
            return basis
    return infer_basis(item)


def has_diary_evidence(item: dict[str, Any]) -> bool:
    evidence = list_of_dicts(item.get("evidence") or [])
    return any(evidence_value(e, "entry_id", "entryId", "id") for e in evidence)


def normalize_dimensions(value: Any) -> list[dict[str, Any]]:
    dimensions: list[dict[str, Any]] = []
    for item in list_of_dicts(value):
        dimensions.append(
            {
                "name": str(item.get("name") or item.get("dimension") or item.get("label") or ""),
                "state": str(item.get("state") or item.get("current_state") or item.get("summary") or ""),
                "trajectory": str(
                    item.get("trajectory")
                    or item.get("movement")
                    or item.get("change")
                    or item.get("trend")
                    or ""
                ),
                "status": str(item.get("status") or item.get("phase") or ""),
                "confidence": str(item.get("confidence") or ""),
                "signals": list_of_strings(item.get("signals") or item.get("markers") or []),
                "evidence": [normalize_evidence_item(e) for e in list_of_dicts(item.get("evidence") or [])],
                "questions": list_of_strings(item.get("questions") or item.get("open_questions") or []),
            }
        )
    return [item for item in dimensions if item["name"] or item["state"] or item["trajectory"]]


def normalize_evidence_item(item: dict[str, Any]) -> dict[str, str]:
    return {
        "entry_id": evidence_value(item, "entry_id", "entryId", "id"),
        "date": evidence_value(item, "date", "entry_date", "entryDate"),
        "snippet": evidence_value(item, "snippet", "excerpt", "quote", "text"),
        "note": evidence_value(item, "note", "reason", "interpretation", "why"),
    }


def evidence_value(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def artifact_summary(row: sqlite3.Row, include_body: bool) -> dict[str, Any]:
    tags = json.loads(row["tags_json"] or "[]")
    dimensions = json.loads(row_get(row, "dimensions_json", "[]") or "[]")
    model = json.loads(row_get(row, "model_json", "{}") or "{}")
    object_count = sum(len(value) for value in model.values() if isinstance(value, list))
    return {
        "id": row["id"],
        "title": row["title"],
        "artifact_type": row["artifact_type"],
        "source": row["source"],
        "date_range": row["date_range"],
        "summary": row["summary"],
        "body_markdown": row["body_markdown"] if include_body else "",
        "dimensions": dimensions,
        "model": model,
        "tags": tags,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "claim_count": int(row_get(row, "claim_count", 0) or 0),
        "evidence_count": int(row_get(row, "evidence_count", 0) or 0),
        "question_count": int(row_get(row, "question_count", 0) or 0),
        "dimension_count": len(dimensions),
        "object_count": object_count,
    }


def evidence_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "entry_id": row["entry_id"],
        "date": row["entry_date"],
        "snippet": row["snippet"],
        "note": row["note"],
    }


def row_get(row: sqlite3.Row, key: str, default: Any = None) -> Any:
    if key not in row.keys():
        return default
    return row[key]


def slugify(value: str) -> str:
    value = value.strip().casefold()
    value = SLUG_RE.sub("-", value).strip("-")
    return value[:64] or "artifact"


def unique_artifact_id(conn: sqlite3.Connection, base_id: str) -> str:
    current = base_id
    for index in range(1, 1000):
        row = conn.execute("SELECT 1 FROM artifacts WHERE id = ?", (current,)).fetchone()
        if row is None:
            return current
        index += 1
        current = f"{base_id}-{index}"
    raise RuntimeError(f"could not create unique artifact id for {base_id}")
