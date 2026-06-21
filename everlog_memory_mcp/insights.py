from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict
from datetime import date
from typing import Any

from .config import Config
from .indexer import scan
from .models import Entry
from .search import entries_in_period, make_excerpt, normalize_query, search_entries
from .tools import privacy_status


THEMES: dict[str, dict[str, Any]] = {
    "agent_memory": {
        "label": "AI / Agent / Memory",
        "terms": ["ai", "agent", "mcp", "模型", "记忆", "memory", "claude", "gpt", "gemini"],
    },
    "journal_self": {
        "label": "Journal / Self Observation",
        "terms": ["日记", "记录", "自己", "自我", "感受", "心路", "变化", "everlog"],
    },
    "product_code": {
        "label": "Product / Code / Work",
        "terms": ["产品", "代码", "项目", "工作", "demo", "github", "开源", "实现"],
    },
    "privacy_safety": {
        "label": "Privacy / Safety",
        "terms": ["隐私", "安全", "本地", "加密", "密码", "指纹", "icloud", "导出"],
    },
    "writing_blog": {
        "label": "Writing / Blog / Public Self",
        "terms": ["博客", "写作", "表达", "公开", "文章", "内容", "输出"],
    },
    "relationships": {
        "label": "Relationships / Others",
        "terms": ["朋友", "关系", "家人", "同学", "别人", "对方", "聊天"],
    },
}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]*|[\u4e00-\u9fff]{2,4}")
TAG_RE = re.compile(r"<[^>]+>")


def build_dashboard(config: Config) -> dict[str, Any]:
    result = scan(config)
    entries = entries_in_period(config, None, None)
    entries.sort(key=lambda entry: entry.entry_date)
    dates = [entry.entry_date for entry in entries]
    total_chars = sum(len(entry.body) for entry in entries)
    attachments = sum(1 for entry in entries if "has_attachment" in entry.tags)
    return {
        "scan": asdict(result),
        "privacy": privacy_status(config),
        "stats": {
            "entry_count": len(entries),
            "date_start": min(dates).isoformat() if dates else None,
            "date_end": max(dates).isoformat() if dates else None,
            "total_chars": total_chars,
            "avg_chars": round(total_chars / len(entries), 1) if entries else 0,
            "long_entries": sum(1 for entry in entries if len(entry.body) > 1000),
            "attachment_entries": attachments,
        },
        "themes": build_themes(config, entries),
        "top_terms": top_terms(entries),
    }


def build_entries(config: Config) -> list[dict[str, Any]]:
    entries = entries_in_period(config, None, None)
    entries.sort(key=lambda entry: entry.entry_date, reverse=True)
    return [entry_card(entry) for entry in entries]


def build_entry(config: Config, entry_id: str) -> dict[str, Any] | None:
    entries = entries_in_period(config, None, None)
    for entry in entries:
        if entry.id == entry_id:
            return {
                **entry_card(entry),
                "body": entry.body,
            }
    return None


def local_answer(config: Config, query: str) -> dict[str, Any]:
    hits = search_entries(config, query, limit=6)
    if not hits:
        return {
            "query": query,
            "answer": "I could not find clear supporting diary evidence for this query.",
            "hits": [],
        }
    dates = [hit.entry.entry_date for hit in hits]
    labels = sorted({theme["label"] for theme in match_themes([hit.entry for hit in hits])})
    answer = (
        f"Found {len(hits)} relevant diary entries from "
        f"{min(dates).isoformat()} to {max(dates).isoformat()}. "
        "This is retrieval evidence, not a personality judgment."
    )
    if labels:
        answer += " Related theme threads: " + ", ".join(labels[:4]) + "."
    return {
        "query": query,
        "answer": answer,
        "hits": [
            {
                "id": hit.entry.id,
                "date": hit.entry.entry_date.isoformat(),
                "title": hit.entry.title,
                "score": hit.score,
                "excerpt": hit.excerpt,
            }
            for hit in hits
        ],
    }


def build_portrait(config: Config) -> dict[str, Any]:
    entries = entries_in_period(config, None, None)
    entries.sort(key=lambda entry: entry.entry_date)
    themes = build_themes(config, entries)
    active = [theme for theme in themes if theme["entry_count"] > 0]
    active.sort(key=lambda theme: (-theme["entry_count"], -theme["score"], theme["label"]))
    dates = [entry.entry_date for entry in entries]
    return {
        "title": "Current Period Portrait",
        "date_range": {
            "start": min(dates).isoformat() if dates else None,
            "end": max(dates).isoformat() if dates else None,
        },
        "positioning": (
            "This portrait is generated from the current Everlog export only. "
            "It should be read as a short-period reflection, not a stable identity profile."
        ),
        "observations": build_observations(active, entries),
        "cadence": build_cadence(entries),
        "next_questions": [
            "Which theme feels alive enough to become a blog post?",
            "Which repeated concern needs action rather than more reflection?",
            "Which private detail should never leave the local vault?",
        ],
    }


def build_themes(config: Config, entries: list[Entry] | None = None) -> list[dict[str, Any]]:
    entries = entries if entries is not None else entries_in_period(config, None, None)
    result = []
    for key, spec in THEMES.items():
        terms = [term.casefold() for term in spec["terms"]]
        matches = []
        score = 0
        for entry in entries:
            haystack = f"{entry.title}\n{' '.join(entry.tags)}\n{entry.body}".casefold()
            entry_score = sum(haystack.count(term) for term in terms)
            if entry_score:
                score += entry_score
                matches.append(
                    {
                        "id": entry.id,
                        "date": entry.entry_date.isoformat(),
                        "title": entry.title,
                        "excerpt": make_excerpt(entry.body, terms, max_chars=300),
                        "score": entry_score,
                    }
                )
        result.append(
            {
                "key": key,
                "label": spec["label"],
                "terms": spec["terms"],
                "score": score,
                "entry_count": len(matches),
                "matches": sorted(matches, key=lambda item: item["date"]),
            }
        )
    return result


def match_themes(entries: list[Entry]) -> list[dict[str, Any]]:
    result = []
    for key, spec in THEMES.items():
        terms = [term.casefold() for term in spec["terms"]]
        score = 0
        for entry in entries:
            haystack = f"{entry.title}\n{' '.join(entry.tags)}\n{entry.body}".casefold()
            score += sum(haystack.count(term) for term in terms)
        if score:
            result.append({"key": key, "label": spec["label"], "score": score})
    return result


def build_observations(themes: list[dict[str, Any]], entries: list[Entry]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    if themes:
        top = themes[0]
        observations.append(
            {
                "claim": f"The strongest visible thread is {top['label']}.",
                "evidence_count": top["entry_count"],
                "confidence": confidence(top["entry_count"], len(entries)),
                "evidence": top["matches"][:3],
            }
        )
    for theme in themes[1:4]:
        observations.append(
            {
                "claim": f"{theme['label']} appears as a secondary recurring thread.",
                "evidence_count": theme["entry_count"],
                "confidence": confidence(theme["entry_count"], len(entries)),
                "evidence": theme["matches"][:2],
            }
        )
    if not observations:
        observations.append(
            {
                "claim": "There is not enough repeated evidence to form a theme-level observation.",
                "evidence_count": 0,
                "confidence": "low",
                "evidence": [],
            }
        )
    return observations


def build_cadence(entries: list[Entry]) -> dict[str, Any]:
    if not entries:
        return {"entry_count": 0, "days_covered": 0, "density": "none"}
    days = (max(entry.entry_date for entry in entries) - min(entry.entry_date for entry in entries)).days + 1
    density = len(entries) / max(days, 1)
    return {
        "entry_count": len(entries),
        "days_covered": days,
        "entries_per_day": round(density, 2),
        "density": "high" if density >= 0.7 else "medium" if density >= 0.3 else "low",
    }


def entry_card(entry: Entry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "date": entry.entry_date.isoformat(),
        "title": entry.title,
        "tags": list(entry.tags),
        "chars": len(entry.body),
        "excerpt": make_excerpt(entry.body, normalize_query(entry.title), max_chars=360),
    }


def top_terms(entries: list[Entry], limit: int = 18) -> list[dict[str, Any]]:
    text = "\n".join(clean_text(entry.body) for entry in entries)
    counter = Counter(token.casefold() for token in TOKEN_RE.findall(text))
    stop = {
        "这个",
        "就是",
        "但是",
        "因为",
        "所以",
        "然后",
        "还是",
        "觉得",
        "自己",
        "可以",
        "一个",
        "没有",
        "如果",
        "不是",
        "really",
        "that",
        "with",
        "this",
    }
    items = [
        {"term": term, "count": count}
        for term, count in counter.most_common(80)
        if term not in stop and count > 1
    ]
    return items[:limit]


def clean_text(text: str) -> str:
    return TAG_RE.sub(" ", text)


def confidence(evidence_count: int, total_entries: int) -> str:
    if total_entries <= 0 or evidence_count <= 1:
        return "low"
    ratio = evidence_count / total_entries
    if ratio >= 0.5:
        return "medium"
    return "low"

