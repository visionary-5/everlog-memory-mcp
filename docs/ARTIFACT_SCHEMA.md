# Artifact Schema

Agents should write structured artifacts with `save_artifact`.

## Minimal Payload

```json
{
  "title": "2026-01-01 to 2026-01-14 thinking evolution",
  "artifact_type": "thinking_evolution",
  "source": "codex",
  "date_range": "2026-01-01..2026-01-14",
  "summary": "This period shows a shift from abstract self-doubt toward evidence-based decisions and clearer project direction.",
  "tags": ["growth", "career", "ai", "memory"],
  "body_markdown": "完整复盘正文，保持可读，但不要大段粘贴日记原文。",
  "model": {
    "threads": [
      {
        "title": "AI and personal value signals",
        "summary": "This thread tracks how the writer connects AI tools, visible output, credibility signals, and market feedback.",
        "movement": "The framing moved from tool usage toward longer-term questions about judgment, leverage, and public evidence of ability.",
        "status": "active",
        "confidence": "high",
        "basis": "diary_evidence",
        "basis_note": "This object is supported by dated Everlog entries with entry ids.",
        "signals": ["AI", "title", "判断力", "市场反馈"],
        "evidence": [
          {
            "date": "2026-06-18",
            "entry_id": "entry_example_001",
            "snippet": "short sanitized diary excerpt",
            "note": "AI became part of the writer's framework for evaluating work and personal leverage."
          }
        ],
        "next_step": "Watch whether this changes project choices, job search behavior, or writing topics."
      }
    ],
    "moments": [
      {
        "title": "A small event made old notes feel like long-term assets",
        "summary": "A concrete loss of past notes changed the meaning of journaling from temporary expression to reusable context.",
        "why_it_matters": "This detail explains why memory infrastructure matters personally, and should not be flattened into a generic productivity theme.",
        "feedback": "Future reflections should separate emotional release, reusable experience, and public writing material.",
        "status": "noted",
        "confidence": "medium-high",
        "basis": "diary_evidence",
        "evidence": [
          {
            "date": "2026-06-07",
            "entry_id": "entry_example_002",
            "snippet": "short sanitized diary excerpt",
            "note": "A concrete event made the value of preserving personal records visible."
          }
        ]
      }
    ],
    "tensions": [
      {
        "title": "Action speed vs careful decision-making",
        "summary": "The writer started valuing low-cost experiments while still keeping a careful decision habit.",
        "movement": "The tension is unresolved and should be tested against future real decisions.",
        "status": "open",
        "confidence": "medium-high",
        "basis": "diary_evidence",
        "evidence": [
          {
            "date": "2026-06-13",
            "entry_id": "entry_example_003",
            "snippet": "short sanitized diary excerpt",
            "note": "Action speed became an explicit theme."
          }
        ]
      }
    ],
    "beliefs": [
      {
        "title": "Ability needs visible evidence",
        "summary": "Ability remains important, but trust, packaging, output, and opportunity windows entered the same model.",
        "movement": "The framing moved from ability alone toward ability plus visible signals.",
        "basis": "diary_evidence",
        "evidence": [
          {
            "date": "2026-06-17",
            "entry_id": "entry_example_004",
            "snippet": "short sanitized diary excerpt",
            "note": "Ability and visible signals were placed in the same decision framework."
          }
        ]
      }
    ],
    "seeds": [
      {
        "title": "How personal value is priced in the AI era",
        "summary": "Turn the relationship between AI, credentials, connections, judgment, and visible output into a public essay.",
        "basis": "diary_evidence",
        "basis_note": "The writing seed is grounded in diary evidence; remove private people, companies, and events before publishing.",
        "private_public": "public-after-sanitized",
        "next_step": "Write a private outline first, then remove names, companies, and diary-specific details."
      }
    ],
    "decisions": [
      {
        "title": "Graduate study vs work path weighting",
        "summary": "The current bias favors one path while keeping other options open.",
        "status": "watching",
        "basis": "diary_evidence"
      }
    ],
    "questions": [
      {
        "title": "Which outputs best make ability visible?",
        "summary": "Projects, writing, research, work output, and reputation signals need to be compared separately.",
        "status": "open",
        "basis": "agent_hypothesis",
        "basis_note": "A follow-up question inferred by the agent; it should be promoted only after future diary evidence supports it."
      }
    ]
  },
  "dimensions": [
    {
      "name": "Career and environment",
      "state": "Career judgment moved from ability alone toward feedback quality, technical density, and visible signals.",
      "trajectory": "The writer moved from abstract self-evaluation toward evaluating real environments.",
      "status": "active",
      "confidence": "high",
      "signals": ["feedback", "technical density", "visible output"],
      "evidence": [
        {
          "date": "2026-06-16",
          "entry_id": "entry_example_005",
          "snippet": "short sanitized diary excerpt",
          "note": "A personal interest, work direction, and technical accumulation connected."
        }
      ],
      "questions": ["Which indicators prove that an environment has useful feedback?"]
    }
  ],
  "claims": [
    {
      "claim": "The writer moved from abstract self-doubt toward evidence-based self-valuation.",
      "interpretation": "The evaluation frame changed from isolated self-questioning to feedback, opportunity windows, and action.",
      "confidence": "medium",
      "evidence": [
        {
          "date": "2026-06-08",
          "entry_id": "entry_example_006",
          "snippet": "short sanitized diary excerpt",
          "note": "The writer connected value judgment with action feedback."
        }
      ]
    }
  ],
  "questions": [
    {
      "question": "How should future major decisions balance careful thinking and earlier action?",
      "status": "open",
      "note": "Track in future entries."
    }
  ]
}
```

## Artifact Types

- `thinking_evolution`
- `period_portrait`
- `theme_thread`
- `blog_seed`
- `product_idea`
- `private_public_boundary`

## Writing Rules

- Claims must cite evidence dates and entry ids when possible.
- Put the primary product intelligence in `model`.
- Use `dimensions` for durable lenses that the UI can track across artifacts.
- Every `model` object must include `basis`.
- Keep direct diary snippets short.
- Put readable prose in `body_markdown`.
- Put machine-readable structure in `model`, `dimensions`, `claims`, `evidence`, `questions`, and `tags`.
- Do not save raw full diary entries.
- Ask the user before calling `save_artifact`.
- Do not present project discussion, current chat context, or product planning as diary-derived insight. If it came from the current conversation, use `basis: "conversation_context"` or `basis: "mixed"` and explain it in `basis_note`.
- For `thinking_evolution` and `period_portrait` artifacts, `model.seeds` should be diary-grounded writing, product, research, or project seeds. Current repo planning should not be saved as a personal diary seed unless the user explicitly asks for a separate `product_idea` artifact.
- A new artifact should be a full updated snapshot of the current self-model, not a delta list. Reuse existing object titles for the same long-running thread, update their state and evidence, and retire stale objects instead of duplicating them under new names.

## Model Objects

The UI treats `model` as the main artifact. Prefer these object groups:

- `threads`: long-running lines of thought, work, life, research, or identity.
- `moments`: specific high-signal details, scenes, reversals, or observations that should not be flattened into a macro summary.
- `tensions`: unresolved conflicts, tradeoffs, or recurring contradictions.
- `beliefs`: ideas whose confidence or framing changed over time.
- `seeds`: writing, product, research, or project ideas that may grow.
- `decisions`: active path choices with options, current bias, and deadlines.
- `questions`: open loops to keep observing in future journals.

Each object should include:

- `title`: short stable name.
- `summary`: current state.
- `movement`: how it changed in this period.
- `why_it_matters`: for moments, why the detail is worth preserving.
- `feedback`: for moments, the agent's direct, evidence-bounded response.
- `status`: active, open, watching, resolved, paused, or draft.
- `confidence`: low, medium, medium-high, high.
- `basis`: one of `diary_evidence`, `prior_artifact`, `conversation_context`, `agent_hypothesis`, or `mixed`.
- `basis_note`: short explanation when the basis is not purely diary evidence.
- `signals`: short tags or markers.
- `evidence`: dates, entry ids, very short snippets, and agent notes.
- `next_step`: optional follow-up action or observation.

Basis rules:

- `diary_evidence`: requires at least one evidence item with `date` and `entry_id`.
- `prior_artifact`: derived from an older saved artifact rather than a fresh diary pass.
- `conversation_context`: comes from the user's current project discussion, not from the diary.
- `agent_hypothesis`: useful inference without direct evidence; keep `status` as `draft` or `watching` and avoid `high` confidence.
- `mixed`: combines diary evidence with another source; explain the split in `basis_note`.

Moment rules:

- Write 3-7 `moments` for each substantial update.
- A moment should be concrete and source-grounded: a scene, surprise, contradiction, quote-level turn, or small observation with high explanatory value.
- Do not use moments for generic advice, therapy-speak, or broad summaries.
- Each moment should explain why the detail matters and what feedback it suggests.
- Moments can later graduate into threads, tensions, seeds, or questions, but they should not be forced into those categories too early.

Agents should read saved artifacts before writing a new one. For daily updates,
read full text only for new entries, then compare against existing `model`
objects from prior artifacts. Old diary entries should be opened only for
evidence checks.

Update protocol:

- Call `list_artifacts` and `read_artifact` for the latest artifact first.
- Call `scan_exports` if the export folder may have changed.
- Read only new or changed entries in full; use searches and period summaries for older evidence.
- Treat the previous `model` as the working memory to update.
- Produce one complete latest model containing kept, changed, new, and retired objects.
- Do not create a second object for the same idea just because the wording changed.

## Recommended Dimensions

For personal growth artifacts, prefer 4-7 durable dimensions:

- `生活状态`: energy, rhythm, sleep, sustainability, emotional load.
- `职业与环境`: internships, teams, feedback quality, visible output.
- `AI 与技术判断`: tools, research direction, labor-market implications.
- `升学/路径策略`: MSc, PhD, job search, option value, deadlines.
- `项目与写作种子`: product ideas, blog themes, experiments.
- `关系与外部反馈`: conversations, mentors, peers, network signals.
- `自我模型`: recurring beliefs, tensions, decision patterns.

Each dimension should answer:

- What is the current state?
- What is changing compared with the previous period?
- Which diary entries support it?
- What should the next artifact continue tracking?
