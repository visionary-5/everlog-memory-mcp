from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path

from .config import Config
from .everlog_json import load_everlog_entry
from .models import Entry, EntryMeta, SearchHit
from .parser import parse_entry
from .store import Store


WORD_RE = re.compile(r"[\w\u4e00-\u9fff]+")


def load_entry(meta: EntryMeta, max_entry_chars: int) -> Entry:
    if meta.source_kind.startswith("everlog_json"):
        entry = load_everlog_entry(meta, max_entry_chars)
        if entry is None:
            raise FileNotFoundError(f"Everlog entry not found: {meta.id}")
        return entry
    return parse_entry(meta.source_path, meta.source_root, max_entry_chars=max_entry_chars)


def search_entries(
    config: Config,
    query: str,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
) -> list[SearchHit]:
    limit = limit or config.max_results
    terms = normalize_query(query)
    if not terms:
        return []

    hits: list[SearchHit] = []
    with Store(config.database_path) as store:
        for meta in store.list_meta(start_date=start_date, end_date=end_date):
            if not meta.source_path.exists():
                continue
            entry = load_entry(meta, config.max_entry_chars)
            haystack = f"{entry.title}\n{' '.join(entry.tags)}\n{entry.body}".casefold()
            score = score_text(haystack, terms)
            if score <= 0:
                continue
            excerpt = make_excerpt(entry.body, terms, max_chars=600)
            hits.append(SearchHit(entry=entry, score=score, excerpt=excerpt))

    hits.sort(key=lambda hit: (-hit.score, hit.entry.entry_date, hit.entry.rel_path))
    return hits[:limit]


def entries_in_period(
    config: Config,
    start_date: date | None,
    end_date: date | None,
    limit: int | None = None,
) -> list[Entry]:
    with Store(config.database_path) as store:
        metas = store.list_meta(start_date=start_date, end_date=end_date, limit=limit)
    entries: list[Entry] = []
    for meta in metas:
        if meta.source_path.exists():
            entries.append(load_entry(meta, config.max_entry_chars))
    return entries


def get_entry(config: Config, entry_id: str) -> Entry | None:
    with Store(config.database_path) as store:
        meta = store.get_meta(entry_id)
    if meta is None or not meta.source_path.exists():
        return None
    return load_entry(meta, config.max_entry_chars)


def compare_periods(
    config: Config,
    period_a: tuple[date | None, date | None],
    period_b: tuple[date | None, date | None],
    theme: str | None = None,
    limit: int | None = None,
) -> dict[str, object]:
    limit = limit or config.max_results
    a_entries = entries_in_period(config, period_a[0], period_a[1])
    b_entries = entries_in_period(config, period_b[0], period_b[1])
    terms = normalize_query(theme or "")

    def summarize(entries: list[Entry]) -> dict[str, object]:
        text = "\n".join(entry.body for entry in entries)
        token_counts = Counter(token.casefold() for token in WORD_RE.findall(text))
        if terms:
            relevant = [
                SearchHit(entry=entry, score=score_text(entry.body.casefold(), terms), excerpt="")
                for entry in entries
            ]
            relevant = [hit for hit in relevant if hit.score > 0]
            relevant.sort(key=lambda hit: (-hit.score, hit.entry.entry_date))
        else:
            relevant = []
        return {
            "entry_count": len(entries),
            "top_terms": token_counts.most_common(12),
            "theme_hits": [
                {
                    "id": hit.entry.id,
                    "date": hit.entry.entry_date.isoformat(),
                    "title": hit.entry.title,
                    "score": hit.score,
                    "excerpt": make_excerpt(hit.entry.body, terms, max_chars=350) if terms else "",
                }
                for hit in relevant[:limit]
            ],
        }

    return {
        "period_a": summarize(a_entries),
        "period_b": summarize(b_entries),
    }


def normalize_query(query: str) -> list[str]:
    query = query.strip().casefold()
    if not query:
        return []
    words = [word for word in WORD_RE.findall(query) if word]
    if len(words) <= 1:
        return [query]
    return words + [query]


def score_text(haystack: str, terms: list[str]) -> int:
    score = 0
    for term in terms:
        if not term:
            continue
        score += haystack.count(term.casefold())
    return score


def make_excerpt(text: str, terms: list[str], max_chars: int = 600) -> str:
    if len(text) <= max_chars:
        return compact(text)
    lower = text.casefold()
    first_pos = -1
    for term in terms:
        pos = lower.find(term.casefold())
        if pos >= 0 and (first_pos < 0 or pos < first_pos):
            first_pos = pos
    if first_pos < 0:
        return compact(text[:max_chars]) + "..."
    start = max(0, first_pos - max_chars // 3)
    end = min(len(text), start + max_chars)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return prefix + compact(text[start:end]) + suffix


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_path_inside(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False
