from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .models import Entry

DATE_RE = re.compile(r"(?P<year>20\d{2}|19\d{2})[-_.]?(?P<month>\d{2})[-_.]?(?P<day>\d{2})")
HASHTAG_RE = re.compile(r"(?<!\w)#([\w\-\u4e00-\u9fff]+)")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def parse_entry(path: Path, source_root: Path, max_entry_chars: int = 12_000) -> Entry:
    raw_bytes = path.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8-sig", errors="replace")
    metadata, body = split_frontmatter(text)
    body = body.strip()
    if len(body) > max_entry_chars:
        body = body[:max_entry_chars].rstrip()

    stat = path.stat()
    rel_path = path.relative_to(source_root).as_posix()
    entry_date = infer_date(metadata, path, stat.st_mtime)
    title = infer_title(metadata, body, path)
    tags = infer_tags(metadata, body)
    entry_id = hashlib.sha256(f"{source_root.resolve()}::{rel_path}".encode("utf-8")).hexdigest()[:16]

    return Entry(
        id=entry_id,
        source_root=source_root,
        source_path=path,
        rel_path=rel_path,
        title=title,
        entry_date=entry_date,
        body=body,
        tags=tags,
        sha256=sha256,
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
    )


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            metadata = parse_simple_yaml(lines[1:idx])
            body = "\n".join(lines[idx + 1 :])
            return metadata, body
    return {}, text


def parse_simple_yaml(lines: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] = []

    def flush_list() -> None:
        nonlocal current_key, current_list
        if current_key is not None:
            data[current_key] = current_list
        current_key = None
        current_list = []

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_key is not None:
            current_list.append(line[4:].strip().strip("\"'"))
            continue
        flush_list()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value == "":
            current_key = key
            current_list = []
            continue
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()]
            data[key] = items
        else:
            data[key] = value.strip("\"'")
    flush_list()
    return data


def infer_date(metadata: dict[str, Any], path: Path, mtime: float) -> date:
    for key in ("date", "created", "created_at", "updated", "updated_at"):
        value = metadata.get(key)
        parsed = parse_date_value(value)
        if parsed is not None:
            return parsed

    match = DATE_RE.search(path.stem)
    if match:
        return date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )

    return datetime.fromtimestamp(mtime).date()


def parse_date_value(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    match = DATE_RE.search(text)
    if match:
        return date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            pass
    return None


def infer_title(metadata: dict[str, Any], body: str, path: Path) -> str:
    title = metadata.get("title")
    if title:
        return str(title).strip()
    match = H1_RE.search(body)
    if match:
        return match.group(1).strip()
    return path.stem


def infer_tags(metadata: dict[str, Any], body: str) -> tuple[str, ...]:
    tags_value = metadata.get("tags") or metadata.get("tag")
    tags: list[str] = []
    if isinstance(tags_value, list):
        tags.extend(str(item).strip().lstrip("#") for item in tags_value if str(item).strip())
    elif isinstance(tags_value, str):
        tags.extend(item.strip().lstrip("#") for item in re.split(r"[, ]+", tags_value) if item.strip())
    tags.extend(match.group(1) for match in HASHTAG_RE.finditer(body))
    seen: set[str] = set()
    unique_tags: list[str] = []
    for tag in tags:
        normalized = tag.strip()
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            unique_tags.append(normalized)
    return tuple(unique_tags)

