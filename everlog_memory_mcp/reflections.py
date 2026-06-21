from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Config


SLUG_RE = re.compile(r"[^a-z0-9\u4e00-\u9fff]+")


@dataclass(frozen=True)
class ReflectionArtifact:
    id: str
    title: str
    artifact_type: str
    created_at: str
    source: str
    date_range: str
    path: Path
    excerpt: str


def reflections_dir(config: Config) -> Path:
    directory = config.database_path.parent / "reflections"
    directory.mkdir(parents=True, exist_ok=True)
    try:
        directory.chmod(0o700)
    except PermissionError:
        pass
    return directory


def save_reflection(
    config: Config,
    title: str,
    body: str,
    artifact_type: str = "period_reflection",
    source: str = "agent",
    date_range: str = "",
) -> ReflectionArtifact:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    artifact_id = f"{created_at[:10]}-{slugify(title)}"
    path = unique_path(reflections_dir(config) / f"{artifact_id}.md")
    frontmatter = {
        "id": path.stem,
        "title": title,
        "type": artifact_type,
        "source": source,
        "date_range": date_range,
        "created_at": created_at,
    }
    content = "---\n" + json.dumps(frontmatter, ensure_ascii=False, indent=2) + "\n---\n\n" + body.strip() + "\n"
    path.write_text(content, encoding="utf-8")
    try:
        path.chmod(0o600)
    except PermissionError:
        pass
    return parse_reflection(path)


def list_reflections(config: Config) -> list[ReflectionArtifact]:
    directory = reflections_dir(config)
    artifacts = [parse_reflection(path) for path in sorted(directory.glob("*.md"))]
    artifacts.sort(key=lambda artifact: artifact.created_at, reverse=True)
    return artifacts


def read_reflection(config: Config, artifact_id: str) -> str | None:
    for artifact in list_reflections(config):
        if artifact.id == artifact_id:
            return strip_frontmatter(artifact.path.read_text(encoding="utf-8"))
    return None


def parse_reflection(path: Path) -> ReflectionArtifact:
    text = path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)
    title = str(meta.get("title") or path.stem)
    artifact_type = str(meta.get("type") or "reflection")
    created_at = str(meta.get("created_at") or "")
    source = str(meta.get("source") or "")
    date_range = str(meta.get("date_range") or "")
    return ReflectionArtifact(
        id=str(meta.get("id") or path.stem),
        title=title,
        artifact_type=artifact_type,
        created_at=created_at,
        source=source,
        date_range=date_range,
        path=path,
        excerpt=excerpt(body),
    )


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    raw_meta = text[4:end].strip()
    body = text[end + 5 :]
    try:
        meta = json.loads(raw_meta)
    except json.JSONDecodeError:
        meta = {}
    return meta, body


def strip_frontmatter(text: str) -> str:
    return split_frontmatter(text)[1].strip()


def excerpt(body: str, max_chars: int = 420) -> str:
    compact = re.sub(r"\s+", " ", body).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars].rstrip() + "..."


def slugify(value: str) -> str:
    value = value.strip().casefold()
    value = SLUG_RE.sub("-", value).strip("-")
    return value[:64] or "reflection"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"too many reflections with base name: {path}")

