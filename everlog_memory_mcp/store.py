from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from .models import Entry, EntryMeta


SCHEMA_VERSION = 1


class Store:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        parent = self.database_path.parent
        parent_created = not parent.exists()
        parent.mkdir(parents=True, exist_ok=True)
        if parent_created:
            try:
                parent.chmod(0o700)
            except PermissionError:
                pass
        self.conn = sqlite3.connect(str(self.database_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.ensure_schema()
        try:
            self.database_path.chmod(0o600)
        except (FileNotFoundError, PermissionError):
            pass

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def ensure_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                source_root TEXT NOT NULL,
                source_path TEXT NOT NULL,
                rel_path TEXT NOT NULL,
                entry_date TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                size INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                source_kind TEXT NOT NULL DEFAULT 'file',
                external_id TEXT,
                title TEXT,
                tags_json TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_entries_path
                ON entries(source_root, rel_path);

            CREATE INDEX IF NOT EXISTS idx_entries_date
                ON entries(entry_date);

            CREATE TABLE IF NOT EXISTS entry_bodies (
                entry_id TEXT PRIMARY KEY REFERENCES entries(id) ON DELETE CASCADE,
                body TEXT NOT NULL
            );
            """
        )
        self.ensure_column("entries", "source_kind", "TEXT NOT NULL DEFAULT 'file'")
        self.ensure_column("entries", "external_id", "TEXT")
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION)),
        )
        self.conn.commit()

    def ensure_column(self, table: str, column: str, definition: str) -> None:
        rows = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        if column not in {row["name"] for row in rows}:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def upsert_entry(self, entry: Entry, store_plaintext: bool) -> bool:
        existing = self.conn.execute(
            "SELECT sha256, mtime_ns FROM entries WHERE id = ?",
            (entry.id,),
        ).fetchone()
        changed = (
            existing is None
            or existing["sha256"] != entry.sha256
            or int(existing["mtime_ns"]) != entry.mtime_ns
        )
        now = datetime.now(timezone.utc).isoformat()
        title = entry.title if store_plaintext else None
        tags_json = json.dumps(entry.tags, ensure_ascii=False) if store_plaintext else None
        self.conn.execute(
            """
            INSERT INTO entries(
                id, source_root, source_path, rel_path, entry_date, sha256,
                size, mtime_ns, source_kind, external_id, title, tags_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                source_root = excluded.source_root,
                source_path = excluded.source_path,
                rel_path = excluded.rel_path,
                entry_date = excluded.entry_date,
                sha256 = excluded.sha256,
                size = excluded.size,
                mtime_ns = excluded.mtime_ns,
                source_kind = excluded.source_kind,
                external_id = excluded.external_id,
                title = excluded.title,
                tags_json = excluded.tags_json,
                updated_at = excluded.updated_at
            """,
            (
                entry.id,
                str(entry.source_root),
                str(entry.source_path),
                entry.rel_path,
                entry.entry_date.isoformat(),
                entry.sha256,
                entry.size,
                entry.mtime_ns,
                entry.source_kind,
                entry.external_id,
                title,
                tags_json,
                now,
            ),
        )
        if store_plaintext:
            self.conn.execute(
                """
                INSERT INTO entry_bodies(entry_id, body)
                VALUES (?, ?)
                ON CONFLICT(entry_id) DO UPDATE SET body = excluded.body
                """,
                (entry.id, entry.body),
            )
        else:
            self.conn.execute("DELETE FROM entry_bodies WHERE entry_id = ?", (entry.id,))
        return changed

    def commit(self) -> None:
        self.conn.commit()

    def list_meta(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
    ) -> list[EntryMeta]:
        where: list[str] = []
        params: list[str | int] = []
        if start_date is not None:
            where.append("entry_date >= ?")
            params.append(start_date.isoformat())
        if end_date is not None:
            where.append("entry_date <= ?")
            params.append(end_date.isoformat())
        sql = "SELECT * FROM entries"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY entry_date ASC, rel_path ASC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [row_to_meta(row) for row in rows]

    def get_meta(self, entry_id: str) -> EntryMeta | None:
        row = self.conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if row is None:
            return None
        return row_to_meta(row)

    def delete_missing(self, seen_ids: set[str]) -> int:
        if not seen_ids:
            row = self.conn.execute("SELECT COUNT(*) AS count FROM entries").fetchone()
            count = int(row["count"])
            self.conn.execute("DELETE FROM entries")
            self.conn.commit()
            return count

        placeholders = ",".join("?" for _ in seen_ids)
        sql = f"DELETE FROM entries WHERE id NOT IN ({placeholders})"
        cur = self.conn.execute(sql, tuple(seen_ids))
        self.conn.commit()
        return int(cur.rowcount)

    def count_entries(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS count FROM entries").fetchone()
        return int(row["count"])

    def database_permissions(self) -> str:
        mode = os.stat(self.database_path).st_mode & 0o777
        return oct(mode)


def row_to_meta(row: sqlite3.Row) -> EntryMeta:
    return EntryMeta(
        id=row["id"],
        source_root=Path(row["source_root"]),
        source_path=Path(row["source_path"]),
        rel_path=row["rel_path"],
        entry_date=date.fromisoformat(row["entry_date"]),
        sha256=row["sha256"],
        size=int(row["size"]),
        mtime_ns=int(row["mtime_ns"]),
        source_kind=row["source_kind"],
        external_id=row["external_id"],
    )
