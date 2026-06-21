from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .everlog_json import iter_everlog_entries
from .parser import parse_entry
from .store import Store


@dataclass(frozen=True)
class ScanResult:
    scanned: int
    changed: int
    deleted: int
    skipped: int
    errors: tuple[str, ...]


def iter_source_files(config: Config) -> Iterable[Path]:
    candidates: list[Path] = []
    for source_dir in config.source_dirs:
        if not source_dir.exists():
            continue
        for path in source_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.name.startswith("."):
                continue
            if is_candidate_path(path, config):
                candidates.append(path)
    yield from sorted(candidates, key=lambda item: (item.stat().st_mtime_ns, str(item)))


def is_candidate_path(path: Path, config: Config) -> bool:
    suffix = path.suffix.lower()
    if config.source_mode == "everlog":
        return path.name == "Entries.json" or suffix == ".zip"
    if suffix in config.allowed_extensions:
        return True
    return path.name == "Entries.json" or suffix == ".zip"


def find_source_root(path: Path, source_dirs: tuple[Path, ...]) -> Path:
    resolved = path.resolve()
    for root in source_dirs:
        root = root.resolve()
        try:
            resolved.relative_to(root)
            return root
        except ValueError:
            continue
    raise ValueError(f"{path} is outside configured source_dirs")


def scan(config: Config, prune_missing: bool = True) -> ScanResult:
    errors: list[str] = []
    scanned = 0
    changed = 0
    skipped = 0
    seen_ids: set[str] = set()

    with Store(config.database_path) as store:
        for path in iter_source_files(config):
            try:
                source_root = find_source_root(path, config.source_dirs)
                entries = entries_for_path(path, source_root, config)
                if not entries:
                    skipped += 1
                    continue
                for entry in entries:
                    seen_ids.add(entry.id)
                    if store.upsert_entry(entry, store_plaintext=config.store_plaintext_index):
                        changed += 1
                    scanned += 1
            except Exception as exc:  # noqa: BLE001 - scanning should keep going.
                skipped += 1
                errors.append(f"{path}: {exc}")
        store.commit()
        deleted = store.delete_missing(seen_ids) if prune_missing else 0

    return ScanResult(
        scanned=scanned,
        changed=changed,
        deleted=deleted,
        skipped=skipped,
        errors=tuple(errors),
    )


def entries_for_path(path: Path, source_root: Path, config: Config):
    if path.name == "Entries.json" or path.suffix.lower() == ".zip":
        entries = iter_everlog_entries(path, source_root, config.max_entry_chars)
        if entries:
            return entries
        return []
    if config.source_mode == "everlog":
        return []
    if path.suffix.lower() == ".json":
        entries = iter_everlog_entries(path, source_root, config.max_entry_chars)
        if entries:
            return entries
        return []
    return [parse_entry(path, source_root, max_entry_chars=config.max_entry_chars)]
