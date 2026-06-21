from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Entry:
    id: str
    source_root: Path
    source_path: Path
    rel_path: str
    title: str
    entry_date: date
    body: str
    tags: tuple[str, ...]
    sha256: str
    size: int
    mtime_ns: int
    source_kind: str = "file"
    external_id: str | None = None


@dataclass(frozen=True)
class EntryMeta:
    id: str
    source_root: Path
    source_path: Path
    rel_path: str
    entry_date: date
    sha256: str
    size: int
    mtime_ns: int
    source_kind: str = "file"
    external_id: str | None = None


@dataclass(frozen=True)
class SearchHit:
    entry: Entry
    score: int
    excerpt: str
