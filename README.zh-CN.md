# everlog-memory-mcp

[English](README.md) | [中文](README.zh-CN.md)

一个非官方的、本地优先的 MCP server 和私有网页，用于基于 Everlog 导出文件做结构化复盘。

`everlog-memory-mcp` 不是另一个日记软件。Everlog 仍然是写日记的地方。这个项目把你导出的日记文件当作本地证据层，让 agent 通过 MCP 查询证据，并把 agent 生成的结构化 artifact 保存成一个本地、版本化的 self-model。

> 状态：早期原型 / 个人 MVP。核心链路已经可以跑，但产品形态、自动化、加密和 UI 仍然需要继续迭代。

## 为什么做

用 LLM 做日记复盘时，结果很容易变成两种东西：原文摘要，或者泛泛的心理建议。这个项目探索的是另一种链路：

```text
Everlog 导出
  -> 本地元数据索引
  -> MCP 证据工具
  -> agent 更新结构化 self-model artifact
  -> 私有成长地图网页
```

目标是保存长期变化：长期线索、高信号 moment、张力、观念变化、决策、问题，以及可能变成写作或研究的种子。

## 功能

- 读取 Everlog JSON 导出、解压后的 `Entries.json` 文件夹、zip 导出、Markdown 和纯文本日记导出。
- 建立本地 SQLite 元数据索引。
- 默认使用 `store_plaintext_index: false`，所以不会把日记正文持久化到元数据数据库里。
- 提供 MCP stdio server，给 agent 使用受限的证据工具。
- 把 agent 生成的结构化 artifact 保存到本地私有 artifact store。
- 提供本地网页：Growth Map、Threads、High-Signal Moments、Open Loops、Seeds、Library 和 Source Vault。

## 不做什么

- 不读取 Everlog 的私有 app 数据库。
- 不绕过 Everlog 密码、Touch ID、iCloud 或 app sandbox。
- 不把你的日记同步到托管服务。
- 浏览器 UI 本身不调用 LLM。
- 它不是云模型服务商的安全边界。如果 agent 把日记片段发给云端模型，模型服务商仍然可能看到这些片段。

## 隐私模型

默认模式比较保守：

- `config.json` 被 Git 忽略，因为里面可能包含私人路径。
- `data/` 被 Git 忽略，因为里面包含本地索引和 artifact。
- 元数据索引只存 id、日期、路径、hash、size、mtime。
- 除非显式开启 plaintext indexing，否则日记正文只在需要时从导出文件读取。
- MCP 工具只返回受限片段，需要 client 或 agent 主动调用。

如果想要更强的本地隐私，可以把 Everlog 导出目录和本项目的 `data/` 放进 FileVault、加密 APFS 卷或加密磁盘镜像里。

## 安装

当前项目只依赖 Python 标准库。

```bash
git clone git@github.com:visionary-5/everlog-memory-mcp.git
cd everlog-memory-mcp
python3 -m everlog_memory_mcp --help
```

创建本地配置文件：

```bash
python3 -m everlog_memory_mcp init-config --path config.json
```

`config.json` 会被 Git 忽略。

## Everlog JSON 导出流程

Everlog 手动导出可能会生成一个 zip 文件，或者一个类似下面名字的解压文件夹：

```text
Everlog Export YYYY-MM-DD_HH-MM-SS
```

导出文件里通常会有 Everlog JSON 数据，例如 `Entries.json`。本项目可以读取两种形式：

- 包含 `Entries.json` 的解压导出文件夹。
- 包含 Everlog JSON 的 zip 文件。

推荐做法：

1. 在 Git 仓库外创建一个稳定的导出收件箱：

   ```text
   ~/Documents/Everlog Exports
   ```

2. 每次新的 Everlog 导出 zip 或解压文件夹都放进这个收件箱。

3. 让项目指向这个稳定收件箱，而不是某一个带时间戳的导出文件夹：

   ```bash
   python3 -m everlog_memory_mcp configure-source \
     "$HOME/Documents/Everlog Exports" \
     --config config.json \
     --source-mode everlog \
     --no-store-plaintext-index \
     --scan
   ```

entry id 基于 Everlog 的条目标识，所以重复导出时应该会更新同一批 entries，而不是把它们重复导入。

如果只是一次性测试，也可以指向某一个解压后的导出文件夹：

```bash
python3 -m everlog_memory_mcp configure-source \
  "$HOME/Documents/Everlog Exports/Everlog Export YYYY-MM-DD_HH-MM-SS" \
  --config config.json \
  --source-mode everlog \
  --no-store-plaintext-index \
  --scan
```

## 更新索引

手动扫描：

```bash
python3 -m everlog_memory_mcp scan --config config.json
```

前台 watcher：

```bash
python3 -m everlog_memory_mcp watch --config config.json --interval 30
```

macOS LaunchAgent：

```bash
python3 -m everlog_memory_mcp install-launch-agent --config config.json --interval 30
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/io.github.visionary5.everlog-memory.watch.plist
```

停止 LaunchAgent：

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/io.github.visionary5.everlog-memory.watch.plist
```

## 本地网页

运行：

```bash
python3 -m everlog_memory_mcp demo --config config.json --host 127.0.0.1 --port 8765
```

打开：

```text
http://127.0.0.1:8765
```

网页本身不调用 LLM，只渲染本地索引和已保存的 artifacts。

## MCP 配置

通过 stdio 启动 MCP server：

```bash
python3 -m everlog_memory_mcp mcp --config config.json
```

生成不同客户端的配置片段：

```bash
python3 -m everlog_memory_mcp mcp-config --client codex --config config.json
python3 -m everlog_memory_mcp mcp-config --client claude-desktop --config config.json
python3 -m everlog_memory_mcp mcp-config --client generic-json --config config.json
```

通用 MCP 配置大概长这样：

```json
{
  "mcpServers": {
    "everlog-memory": {
      "command": "python3",
      "args": [
        "-m",
        "everlog_memory_mcp",
        "mcp",
        "--config",
        "/absolute/path/to/everlog-memory-mcp/config.json"
      ],
      "cwd": "/absolute/path/to/everlog-memory-mcp"
    }
  }
}
```

## MCP 工具

证据工具：

- `privacy_status`
- `scan_exports`
- `search_entries`
- `get_entry`
- `summarize_period_context`
- `trace_theme`
- `compare_periods`

Artifact 工具：

- `save_artifact`
- `list_artifacts`
- `read_artifact`
- `save_reflection`
- `list_reflections`
- `read_reflection`

agent 应该引用日期和 entry id，保持直接引用很短，区分证据和解释，并更新已有 self-model 对象，而不是不断创建重复 summary。

## Agent Artifact 工作流

推荐的 agent 链路：

1. 用 `list_artifacts` 和 `read_artifact` 读取最新 artifact。
2. 运行 `scan_exports`。
3. 只完整读取新增条目，或者为了核验证据而读取必要旧条目。
4. 更新已有 self-model，而不是追加一篇新的独立总结。
5. 用 `save_artifact` 保存一个完整的新 artifact。

model 应该包含：

- `threads`：长期思考、工作、生活、研究或身份线索。
- `moments`：不应该被宏观总结压掉的具体高信号细节。
- `tensions`：反复出现的冲突、权衡和未解决张力。
- `beliefs`：信念、判断或框架的变化。
- `seeds`：有日记证据支撑的写作、产品、研究或项目种子。
- `decisions`：仍在权衡的路径选择。
- `questions`：后续日记需要继续观察的问题。

每个对象都带有 `basis` 元数据，例如 `diary_evidence`、`prior_artifact`、`conversation_context`、`agent_hypothesis` 或 `mixed`，这样 UI 可以区分哪些是日记证据支撑，哪些只是推测或项目讨论。

参考 [Artifact Schema](docs/ARTIFACT_SCHEMA.md) 和
[Agent Demo Prompts](docs/AGENT_DEMO.md)。

## 当前产品形态

- `Growth Map`：当前由日记证据支撑的 self-model 概览。
- `High-Signal Moments`：agent 不应该压缩掉的具体细节。
- `Threads`：长期变化的二级页面。
- `Open Loops`：需要继续追踪的决策和问题。
- `Seeds`：有日记证据支撑、可能变成写作/研究/项目的想法。
- `Library`：已保存 artifact 的版本历史。
- `Source Vault`：只用于核验证据的原始日记入口。

## Roadmap

近期方向：

- 更稳定的跨 artifact 更新协议。
- 稳定 object id 和 artifact diff。
- 对重复 thread 和 seed 做去重。
- 更可靠地监听重复 Everlog 导出。
- artifact store 加密。
- 本地或混合检索，避免 agent 每次重读旧日记。
- 更成熟的私有网页 UI 和 object 级历史页面。

查看 [Iteration Plan](docs/ITERATION_PLAN.md) 了解当前设计、工程和产品创新三条线的拆分。

## 文档

- [Everlog integration](docs/EVERLOG.md)
- [Real Everlog setup](docs/REAL_EVERLOG_SETUP.md)
- [Product architecture](docs/ARCHITECTURE.md)
- [Local memory system](docs/MEMORY_SYSTEM.md)
- [Artifact schema](docs/ARTIFACT_SCHEMA.md)
- [Agent demo prompts](docs/AGENT_DEMO.md)
- [Iteration plan](docs/ITERATION_PLAN.md)
- [Reflection workflow](docs/REFLECTION_WORKFLOW.md)
- [Security notes](docs/SECURITY.md)
- [MCP client setup](docs/MCP_CLIENTS.md)
- [Product direction](docs/PRODUCT_DIRECTION.md)

## License

MIT.
