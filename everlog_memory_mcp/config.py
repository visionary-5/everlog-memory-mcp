from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_ALLOWED_EXTENSIONS = (".md", ".markdown", ".txt", ".json", ".zip")


@dataclass(frozen=True)
class Config:
    source_dirs: tuple[Path, ...]
    database_path: Path
    allowed_extensions: tuple[str, ...] = DEFAULT_ALLOWED_EXTENSIONS
    source_mode: str = "mixed"
    store_plaintext_index: bool = False
    max_entry_chars: int = 12_000
    max_results: int = 8

    @classmethod
    def from_file(cls, path: str | Path) -> "Config":
        config_path = Path(path).expanduser().resolve()
        data = json.loads(config_path.read_text(encoding="utf-8"))
        base_dir = config_path.parent
        return cls.from_dict(data, base_dir=base_dir)

    @classmethod
    def from_dict(cls, data: dict[str, Any], base_dir: Path | None = None) -> "Config":
        if "source_dirs" not in data or not data["source_dirs"]:
            raise ValueError("config requires a non-empty source_dirs list")
        if "database_path" not in data:
            raise ValueError("config requires database_path")

        source_dirs = tuple(_resolve_path(item, base_dir) for item in data["source_dirs"])
        allowed_extensions = tuple(
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in data.get("allowed_extensions", DEFAULT_ALLOWED_EXTENSIONS)
        )
        return cls(
            source_dirs=source_dirs,
            database_path=_resolve_path(data["database_path"], base_dir),
            allowed_extensions=allowed_extensions,
            source_mode=str(data.get("source_mode", "mixed")),
            store_plaintext_index=bool(data.get("store_plaintext_index", False)),
            max_entry_chars=int(data.get("max_entry_chars", 12_000)),
            max_results=int(data.get("max_results", 8)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_dirs": [str(path) for path in self.source_dirs],
            "database_path": str(self.database_path),
            "allowed_extensions": list(self.allowed_extensions),
            "source_mode": self.source_mode,
            "store_plaintext_index": self.store_plaintext_index,
            "max_entry_chars": self.max_entry_chars,
            "max_results": self.max_results,
        }

    def write(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        target.chmod(0o600)
        return target


def _resolve_path(value: str, base_dir: Path | None) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    return path.resolve()


def write_example_config(path: str | Path) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    example = {
        "source_dirs": [str(target.parent / "examples")],
        "database_path": str(target.parent / "data" / "index.sqlite3"),
        "allowed_extensions": list(DEFAULT_ALLOWED_EXTENSIONS),
        "source_mode": "mixed",
        "store_plaintext_index": False,
        "max_entry_chars": 12000,
        "max_results": 8,
    }
    target.write_text(json.dumps(example, indent=2) + "\n", encoding="utf-8")
    target.chmod(0o600)
    return target


def configure_source(
    config_path: str | Path,
    source_dirs: list[str],
    database_path: str | None = None,
    create_dirs: bool = False,
    source_mode: str | None = None,
    store_plaintext_index: bool | None = None,
) -> Config:
    target = Path(config_path).expanduser().resolve()
    base_dir = target.parent

    if target.exists():
        existing = Config.from_file(target)
    else:
        existing = Config(
            source_dirs=tuple(),
            database_path=(base_dir / "data" / "index.sqlite3").resolve(),
        )

    resolved_sources = tuple(Path(item).expanduser().resolve() for item in source_dirs)
    if create_dirs:
        for source_dir in resolved_sources:
            source_dir.mkdir(parents=True, exist_ok=True)

    missing = [str(path) for path in resolved_sources if not path.exists()]
    if missing:
        raise ValueError(
            "source directory does not exist; create it first or pass --create: "
            + ", ".join(missing)
        )

    configured = Config(
        source_dirs=resolved_sources,
        database_path=_resolve_path(database_path, base_dir) if database_path else existing.database_path,
        allowed_extensions=merge_allowed_extensions(existing.allowed_extensions),
        source_mode=source_mode or existing.source_mode,
        store_plaintext_index=(
            existing.store_plaintext_index
            if store_plaintext_index is None
            else store_plaintext_index
        ),
        max_entry_chars=existing.max_entry_chars,
        max_results=existing.max_results,
    )
    configured.write(target)
    return configured


def merge_allowed_extensions(extensions: tuple[str, ...]) -> tuple[str, ...]:
    merged = list(extensions)
    seen = {item.lower() for item in merged}
    for ext in DEFAULT_ALLOWED_EXTENSIONS:
        if ext not in seen:
            merged.append(ext)
            seen.add(ext)
    return tuple(merged)
