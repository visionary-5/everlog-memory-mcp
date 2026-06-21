# Agent Demo

The browser UI is only a local dashboard. The real demo is asking a strong agent
to use the Everlog MCP server as an evidence layer.

## Example local state

- Codex MCP server: `everlog-memory`
- Claude MCP server: `everlog-memory`
- Source inbox: `/path/to/everlog/exports`
- Current entries indexed: depends on your local export
- Plaintext body persistence: disabled

## Codex

From this project:

```bash
cd /path/to/everlog-memory-mcp
codex
```

Useful update prompt:

```text
请使用 everlog-memory MCP server。

我不要日记浏览器、原文摘要、top terms，也不要泛泛鼓励。请把 Everlog
导出当作证据层，把已保存的 artifacts 当作长期记忆层，更新一份
private growth map。先不要保存，先给我预览。

操作顺序：
1. 先调用 list_artifacts，读取最新 artifact。
2. 调用 scan_exports，确认 Everlog 导出是否有变化。
3. 只完整读取新增或需要核验证据的 entry；不要为了复盘重新吞掉所有旧日记。
4. 把最新 artifact 里的 model 当作当前工作记忆来更新，而不是简单叠加一批新对象。

请输出：
1. model.threads：长期线索，不要只按关键词分组。
2. model.moments：3-7 个高信号细节，防止把日记压扁成宏大 summary。
3. model.tensions：未解决的张力或矛盾。
4. model.beliefs：这段时间发生变化的判断。
5. model.seeds：可能变成博客、产品、研究或项目的种子。
6. model.decisions：仍在权衡的路径选择。
7. model.questions：后续日记要继续观察的问题。
8. supporting claims/dimensions/evidence：用于支撑 model，不要喧宾夺主。

规则：
- 引用日期和 entry id。
- 每个 model 对象都必须写 `basis`：
  `diary_evidence` / `prior_artifact` / `conversation_context` /
  `agent_hypothesis` / `mixed`。
- 如果内容来自这次产品讨论、项目上下文或你的推测，不要伪装成日记证据；
  请用 `conversation_context`、`agent_hypothesis` 或 `mixed`，并写
  `basis_note`。
- `diary_evidence` 必须有 evidence 数组，并包含 date 和 entry_id。
- 对同一个长期线索，复用原来的 title，更新 summary/movement/evidence；
  不要因为措辞变化就创建一个重复 thread。
- 输出的是“完整最新版 self-model”，不是 delta patch，也不是新增对象列表。
- `model.moments` 必须具体：场景、反常点、微小转折、值得反馈的细节；
  不要写成心理辅导、泛泛建议或宏观主题的另一种说法。
- `model.seeds` 只放日记证据支撑出来的写作、研究、产品或项目种子；
  当前 repo/产品讨论不要放进个人日记 self-model。
- 直接摘录必须很短，不要粘贴大段日记。
- 不要给人格诊断，不要把我定义成某种固定的人。
- 不要把复杂信息极致压缩成几句空话；宁可保留结构和张力。
- 如果我确认保存，请调用 `save_artifact`，并严格使用
  `docs/ARTIFACT_SCHEMA.md` 里的结构，尤其要写 `model`。
```

## Claude CLI

From this project:

```bash
cd /path/to/everlog-memory-mcp
claude
```

Useful first prompt:

```text
请使用 everlog-memory MCP server 分析当前 Everlog 导出。

我要的是结构化 private growth map，不是日记原文 dump：
- 读取新增日记，但也要先查看已经保存的 artifacts。
- 判断哪些旧 thread/tension/belief/seed 需要更新。
- 提取 3-7 个 high-signal moments：具体、细节化、有反馈价值。
- 判断哪些新对象应该加入 model。
- 复用旧对象，不要为同一个主题重复创建对象。
- 输出完整最新版 self-model，不要只输出新增 delta。
- 哪些内容只是私人心路，哪些可能变成博客/产品/研究方向？
- 请把结果组织成 model、claims、dimensions、evidence、questions。

请引用日期和 entry id，证据片段保持很短。每个 model 对象都要写
`basis` 和必要的 `basis_note`：不要把当前对话或项目规划误写成日记证据。
```

After getting a good answer, ask:

```text
请把这份复盘按 save_artifact 的结构保存成本地 artifact，标题为
"2026-06-07 至 2026-06-20 思维变化复盘"，artifact_type 写
thinking_evolution，source 写 codex 或 claude。请一定包含 model 字段，
不要只保存 body_markdown，也不要只保存 dimensions。
```

## What "good" looks like

Good output should look like a reflection memo:

- Claim: a cautious observation.
- Evidence: dates and short excerpts.
- Interpretation: why the pattern might matter.
- Next question: what to ask or track next.

Bad output:

- Long pasted diary text.
- Generic encouragement.
- Personality labels.
- Top-term lists without interpretation.
- Project ideas or conversation context shown as diary-derived facts.

## Product direction

The dashboard is not the final experience. It is only a debug/status surface. The
real product loop is:

```text
strong agent generates reflection -> save_artifact -> UI reviews artifacts
```
