---
name: agent-memory-kit
description: 给「你正在构建的产品 agent」挂运行时记忆层（记忆四角色：Doer 留 trace → Reflector 评估提炼 → Store 持久化 → 检索注入回 Doer）。当用户说"给这个 agent 加记忆/挂记忆层/让 agent 记住经验教训/上次踩的坑下次别再踩/接入 agent-memory-kit"时使用。落地物：{dir}/memory/ 模板树（retrieval 检索注入 + evolve 闭环优化两块现成，reflector/librarian 接口占位）。注意：这是运行时记忆（产品 agent 的），不是 Claude Code 自己的开发时记忆——后者由 harness-init 的 L1 层负责。
---

# Agent Memory Kit 挂载 Agent

把 [agent-memory-kit](https://github.com/libaoming/agent-memory-kit) 的运行时记忆层脚手架挂进目标项目。**诚实定位：这是脚手架不是中间件**——retrieval 和 evolve 两块开箱可跑，critic/librarian 是接口占位，评估维度和持久层 schema 仍需按业务填。

## 记忆四角色（落地前先给用户看这张图）

```
Doer（用户的 agent · 无状态执行）
   │ 留下 trace
   ▼
Reflector（第二组 agent · 独立 context）
   ├─ critic   : 评估哪里错      → reflector/   🟡 接口占位
   └─ librarian: 提炼成长期教训   → librarian/   🟡 接口占位
   ▼
Store（持久记忆 *.md）
   ▼
检索注入回 Doer                  → retrieval/    ✅ 现成
                                   evolve/       ✅ 现成（prompt 闭环优化）
```

## 执行流程

### 第 0 步 · 确认目标
1. **目标项目目录**（通常是当前项目；若由 `/harness-kit:harness-init` 的 1b 步触发，目录已知）
2. 确认项目里有要挂记忆的 agent（Doer 是谁、trace 长什么样、store 打算放哪）

### 第 1 步 · 复制模板树
本 skill 目录下 `templates/` 即模板源，复制到 `{dir}/memory/`：

| 源 | 目标 | 作用 |
|---|---|---|
| `templates/MEMORY.md` | `{dir}/memory/MEMORY.md`（填 `{{PROJECT}}` `{{OWNER}}` `{{DATE}}`） | 记忆四角色纪律（运行时/开发时分两节） |
| `templates/retrieval/` | `{dir}/memory/retrieval/` | FTS5 + 时间衰减 + RRF 检索注入；复制 `config.example.json` 为项目 config 并改指向项目 store |
| `templates/evolve/` | `{dir}/memory/evolve/` | fixture → agent → judge → TSV 记账的闭环优化（详细用法见 `/harness-kit:autoevolve`） |
| `templates/reflector/` + `templates/librarian/` | 同名目录 | critic 评估 / 持久层接口占位，按各自 README 接业务自己的质检器/后端 |

### 第 2 步 · 接进项目骨架（若项目是 harness 项目）
- `features.json` 加一个 `memory-layer` feature 桩（status: `pending`）
- 项目 `CLAUDE.md` 的 L1 段补一行：「Doer 运行前先 `memory_search` 注入历史教训，运行后经 Reflector 写 store」

### 第 3 步 · 报告 + 指路
- 输出落地的文件树 + 哪两块能直接跑、哪两块要业务接线
- 冒烟命令：`python3 memory/retrieval/memory_search.py "测试关键词" --config <项目config> --top 5`
- 真实接线范例：https://github.com/libaoming/agent-memory-kit/tree/main/examples/recruit-voice-runtime

## 注意事项
- **别和开发时记忆混了**：本 kit 服务「用户 build 的产品 agent」；Claude Code 自己的跨会话接力靠 harness-init 的 L1（CLAUDE.md + STATUS + Auto Memory），两层不重复造
- 目标目录已有 `memory/` 时先确认再合并，不静默覆盖
- retrieval/evolve 均为纯标准库 + claude CLI 订阅模式，不需要额外 API key
