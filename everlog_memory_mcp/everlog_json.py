from __future__ import annotations

import hashlib
import html
import json
import re
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .models import Entry, EntryMeta

EVERLOG_REQUIRED_KEYS = {"entries", "journals", "version"}
TAG_RE = re.compile(r"<[^>]+>")
LINE_RE = re.compile(r"\s+")


def iter_everlog_entries(path: Path, source_root: Path, max_entry_chars: int) -> list[Entry]:
    if path.suffix.lower() == ".zip":
        return iter_everlog_entries_from_zip(path, source_root, max_entry_chars)
    if path.name == "Entries.json" or path.suffix.lower() == ".json":
        data = read_json_file(path)
        if looks_like_everlog_export(data):
            return entries_from_export(data, path, source_root, path.name, max_entry_chars)
    return []


def load_everlog_entry(meta: EntryMeta, max_entry_chars: int) -> Entry | None:
    entries = iter_everlog_entries(meta.source_path, meta.source_root, max_entry_chars)
    for entry in entries:
        if entry.external_id == meta.external_id or entry.id == meta.id:
            return entry
    return None


def read_json_file(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def iter_everlog_entries_from_zip(
    path: Path,
    source_root: Path,
    max_entry_chars: int,
) -> list[Entry]:
    entries: list[Entry] = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            if not member.endswith(".json"):
                continue
            raw = archive.read(member)
            data = json.loads(raw.decode("utf-8-sig"))
            if looks_like_everlog_export(data):
                entries.extend(entries_from_export(data, path, source_root, member, max_entry_chars))
    return entries


def looks_like_everlog_export(data: Any) -> bool:
    return isinstance(data, dict) and EVERLOG_REQUIRED_KEYS.issubset(data.keys())


def entries_from_export(
    data: dict[str, Any],
    source_path: Path,
    source_root: Path,
    member_name: str,
    max_entry_chars: int,
) -> list[Entry]:
    journals = {
        str(item.get("identifier")): str(item.get("name") or "")
        for item in data.get("journals", [])
        if isinstance(item, dict) and item.get("identifier")
    }
    stat = source_path.stat()
    rel_source = source_path.relative_to(source_root).as_posix()
    result: list[Entry] = []
    for raw_entry in data.get("entries", []):
        if not isinstance(raw_entry, dict):
            continue
        result.append(
            entry_from_raw(
                raw_entry,
                journals=journals,
                source_path=source_path,
                source_root=source_root,
                rel_source=rel_source,
                member_name=member_name,
                size=stat.st_size,
                mtime_ns=stat.st_mtime_ns,
                max_entry_chars=max_entry_chars,
            )
        )
    return result


def entry_from_raw(
    raw_entry: dict[str, Any],
    journals: dict[str, str],
    source_path: Path,
    source_root: Path,
    rel_source: str,
    member_name: str,
    size: int,
    mtime_ns: int,
    max_entry_chars: int,
) -> Entry:
    external_id = str(raw_entry.get("identifier") or "")
    if not external_id:
        external_id = hashlib.sha256(
            json.dumps(raw_entry, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
    entry_id = hashlib.sha256(f"everlog::{external_id}".encode("utf-8")).hexdigest()[:16]
    content = plain_text(str(raw_entry.get("content") or ""))
    if len(content) > max_entry_chars:
        content = content[:max_entry_chars].rstrip()
    entry_date = parse_everlog_date(raw_entry.get("date") or raw_entry.get("dateCreated"))
    title = infer_title(content, entry_date)
    tags = infer_tags(raw_entry, journals)
    entry_hash = hashlib.sha256(
        json.dumps(raw_entry, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    return Entry(
        id=entry_id,
        source_root=source_root,
        source_path=source_path,
        rel_path=f"{rel_source}!{member_name}#{external_id}",
        title=title,
        entry_date=entry_date,
        body=content,
        tags=tags,
        sha256=entry_hash,
        size=size,
        mtime_ns=mtime_ns,
        source_kind="everlog_json_zip" if source_path.suffix.lower() == ".zip" else "everlog_json",
        external_id=external_id,
    )


def parse_everlog_date(value: Any) -> date:
    if not value:
        return date.today()
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    match = re.search(r"(19\d{2}|20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", text)
    if match:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return date.today()


def plain_text(content: str) -> str:
    content = content.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    content = TAG_RE.sub("", content)
    content = html.unescape(content)
    lines = [LINE_RE.sub(" ", line).strip() for line in content.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def infer_title(content: str, entry_date: date) -> str:
    for line in content.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:80]
    return entry_date.isoformat()


def infer_tags(raw_entry: dict[str, Any], journals: dict[str, str]) -> tuple[str, ...]:
    tags: list[str] = []
    journal_id = str(raw_entry.get("journal") or "")
    journal_name = journals.get(journal_id)
    if journal_name:
        tags.append(f"journal:{journal_name}")
    if str(raw_entry.get("isBookmarked") or "").lower() == "true":
        tags.append("bookmarked")
    attachments = raw_entry.get("attachments") or []
    if isinstance(attachments, list) and attachments:
        tags.append("has_attachment")
        for attachment in attachments:
            if isinstance(attachment, dict) and attachment.get("type"):
                tags.append(f"attachment:{attachment['type']}")
    return tuple(dict.fromkeys(tags))

