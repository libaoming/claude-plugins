---
name: harness-init
description: 项目初始化的唯一入口（替代单独跑 /init）。用 harness 方法论 + 4 层防御体系，对空目录新建 OR 已有代码库纳管都适用。当用户要"新建项目/起一个项目/搭骨架/抽离成独立项目/bootstrap/给老项目补 CLAUDE.md/纳管已有仓库/初始化项目"时使用。自动生成 CLAUDE.md（含上下文隔离 subagent 纪律）+ STATUS + PRD/SPEC/architecture 桩 + features.json + M1 三件套 + fixtures + 项目专属脏活隔离子 agent；已有代码时先做 /init 式扫描再合并。可按需挂载两个独立 kit：要构建带记忆的 agent 时挂 agent-memory-kit（运行时记忆层：检索注入+闭环优化），要做上下文审计时挂 context-engineering-kit（CONTEXT.md 7 层表）。
---

# Harness 项目脚手架 Agent

把 [harness 方法论](https://github.com/libaoming/harness-kit) + **4 层防御体系**一次性 scaffold 进新项目。目标：用户跑一次，新项目就带齐全套骨架 + 上下文隔离能力，不靠我每次手写。

## 4 层防御体系（生成物会把这套写进项目 CLAUDE.md）

| 层 | 内容 | 落地物 |
|---|---|---|
| **L1 持久化层** | 业务语义/规则/进度从 LLM 记忆迁到文件 | `CLAUDE.md` + `STATUS.md` + Auto Memory |
| **L2 方法论层** | 单一事实源 + 可验证 + 线性推进 | `features.json` + `M1/` 三件套 + fixture 先于代码 + **技术方案先于开发（`docs/proposals/` 待评估，用户评估通过才开发）** + verify 纪律 |
| **L3 自动化钩子层** | 确定性自动化（按需） | Hooks（session 注入 / 同步 / 格式化），项目级 `.claude/settings.json` |
| **L4 上下文隔离层** | 脏活派子 agent，只回结论，主 context 干净 | CLAUDE.md「上下文隔离纪律」段 + `.claude/agents/{proj}-ops.md` 只读运维子 agent |

> **三 kit 关系**：harness-kit（本 skill 的 `templates/`）是**默认核心**——L1-L4，所有项目都带。另有两个**按需挂载的扩展**，由第 0b/1b 步的开关决定挂不挂，保持核心轻量：
> - **agent-memory-kit**（运行时记忆层 · 记忆四角色：检索注入 + 闭环优化）— 构建「带记忆的产品 agent」时挂。本 plugin 内置为独立 skill `/harness-kit:agent-memory-kit`，方法论仓库 https://github.com/libaoming/agent-memory-kit
> - **context-engineering-kit**（CONTEXT.md · 7 层上下文构成审计）— 要做 context 工程时挂。**plugin 暂不内置**，需本地 clone 该 kit 才可挂载。
>
> 此外核心内还有一个**可选模块**（非独立 kit，模板就在本 skill `templates/`）：**并行编排层**（`BOARD.md`）——一个里程碑要多 agent 并行时挂，单线接力不挂。由第 0b 第 8 问、第 1c 步控制。
>
> ⚠️ 别混：L1 的 Auto Memory 是**开发时记忆**（Claude Code 跨会话接力）；agent-memory-kit 是**运行时记忆**（你 build 的产品 agent 记住经验）。两者不同层，不重复造。

## 执行流程

本 skill 是项目初始化的**唯一入口**——无论空目录新建、还是已有代码库纳管，都走它，**不需要再单独跑 `/init`**（`/init` 的"扫码生成 CLAUDE.md"能力已内化进第 0 步的「已有代码」分支）。

### 第 0 步 · 探测目录 + 收集信息

**0a 探测目标目录**（先 `ls -A {dir} 2>/dev/null`）：
- **空目录 / 不存在** → 走 **A 路线（全新 scaffold）**：第 1-3 步原样执行。
- **已有代码**（有源码/git/package 文件）→ 走 **B 路线（已有代码库纳管）**：
  1. 先做 `/init` 式扫描——读项目结构、入口、依赖、命令，**理解这个仓库是什么**。
  2. 生成 CLAUDE.md 时：把扫描到的"项目身份 / 仓库结构 / 常用命令"**填进** `templates/CLAUDE.md` 的对应位置，而不是用占位符空壳——即 init 的产出 + harness 的 4 层结构**合并成一份** CLAUDE.md。
  3. 已存在的文件（如旧 CLAUDE.md / README）**先确认再合并**，绝不静默覆盖用户内容。
  4. PRD/SPEC/architecture：若仓库已有等价文档则跳过桩，否则补桩。features.json：从现有代码反推已完成的 feature（status 标 `passing` 需谨慎，没 verify 过只标 `in_progress`）。

**0b 收集信息**（用 AskUserQuestion 或对话）：
1. **项目名**（kebab-case，如 `voice-recruit`）
2. **一句话定位**（项目是什么 / 给谁 / 解决什么）
3. **目标目录**（默认 `~/{项目名}`；若是"从 X 抽离"则确认新目录）
4. **首个里程碑名**（默认 `M1`）
5. **是否要项目专属运维子 agent**（默认要——L4 的"脏活隔离"载体）
6. **这项目要构建一个「带记忆的 agent」吗？**（默认否）——是则挂 `agent-memory-kit`（运行时记忆层：检索注入 + 闭环优化 + 记忆纪律）
7. **要做 context 审计吗？**（默认否）——是则挂 `context-engineering-kit`（CONTEXT.md 7 层上下文构成表）
8. **这个里程碑会有多个 agent 并行干吗？**（默认否）——是则挂**并行编排层**（`BOARD.md` 状态板：认领表 + 星型只写不读 + Merge Gate）；单线接力别挂，`STATUS.md` 就够

> ⚠️ 触发场景：凡是"抽离/拆分/独立成项目/migrate to standalone/分仓"——只要产生新顶层目录就是新建项目，必须走本 skill，别只搬文件 + 加 README（踩过的坑：搬完文件没骨架，三天后没人记得这项目到哪了）。

### 第 1 步 · scaffold 机械文件（从模板复制 + 填占位符）
本 skill 目录下 `templates/` 有全部模板。占位符：`{{PROJECT}}` `{{POSITIONING}}` `{{DATE}}`（今天，先 `date +%Y-%m-%d`）`{{MILESTONE}}` `{{OWNER}}`（取 `git config user.name`，取不到就问用户）。

按下表把模板写入目标目录（复制 → 替换占位符 → 写文件）：

| 模板 | 目标 | 层 |
|---|---|---|
| `templates/CLAUDE.md` | `{dir}/CLAUDE.md` | L1+L4（核心，含 4 层说明 + 隔离纪律 + 子 agent 铁律） |
| `templates/STATUS.md` | `{dir}/STATUS.md` | L1 |
| `templates/features.json` | `{dir}/features.json` | L2 |
| `templates/M1_init.sh` | `{dir}/{MILESTONE}/init.sh`（`chmod +x`） | L2 |
| `templates/M1_AGENTS.md` | `{dir}/{MILESTONE}/AGENTS.md` | L2 |
| `templates/M1_PROGRESS.md` | `{dir}/{MILESTONE}/PROGRESS.md` | L2 |
| `templates/fixtures_README.md` | `{dir}/fixtures/README.md` | L2 |
| `templates/agent_ops.md` | `{dir}/.claude/agents/{PROJECT}-ops.md` | L4（项目专属只读运维子 agent；用户选要才建） |
| `templates/settings.local.json` | `{dir}/.claude/settings.local.json` | L3（注册**一对 Stop hook**：①增量追加进度 ②防造假收口闸；local 不入 git） |
| `templates/hooks/stop-progress-append.sh` | `{dir}/.claude/hooks/stop-progress-append.sh`（`chmod +x`） | L3（hook①脚本本体：每轮把用户请求追加到进度文件「增量流水」区，扛关电脑，随项目走不依赖全局路径） |
| `templates/hooks/stop-verify-claims.py` | `{dir}/.claude/hooks/stop-verify-claims.py`（`chmod +x`） | L3（hook②脚本本体：防造假收口闸，末轮"已写/File created + 文件名"或交付表 `path`（N 行）逐一 `test -f`，缺失则 exit 2 拒绝收口喂回缺失清单；缺 python3 自动降级 no-op） |

### 第 1b 步 · 按需挂载 memory / context kit（仅当 0b 选了对应开关）

harness-kit 保持轻量，运行时记忆与 context 审计是**独立扩展、按需挂载**，不无脑全塞。

- **选了「带记忆 agent」** → 调用本 plugin 的 `/harness-kit:agent-memory-kit` skill 完成挂载（模板树随该 skill 自带，会复制到 `{dir}/memory/` 并在 `features.json` 加 `memory-layer` 桩、CLAUDE.md L1 段补记忆纪律一行）。真实接线范例见 https://github.com/libaoming/agent-memory-kit/tree/main/examples/recruit-voice-runtime （自包含可独立跑）。
- **选了「context 审计」** → 需本地有 context-engineering-kit（plugin 未内置）：从 `~/context-engineering-kit/templates/CONTEXT.md` 复制到 `{dir}/CONTEXT.md`，引导填 7 层上下文构成表；本地没有该 kit 就明确告知用户跳过此挂载。

### 第 1c 步 · 按需挂载并行编排层（仅当 0b 第 8 问选了「多 agent 并行」）

默认**不挂**——并行是少数场景，核心保持单线轻量。选了才把 `templates/BOARD.md` 复制到 `{dir}/BOARD.md`（替换 `{{MILESTONE}}` `{{DATE}}`），它和 `STATUS.md` 正交：`STATUS.md` 是接力视角，`BOARD.md` 是 N 个 agent 此刻各自到哪。

| 模板 | 目标 | 说明 |
|---|---|---|
| `templates/BOARD.md` | `{dir}/BOARD.md` | 多 agent 并行状态板：认领表（防撞车）+ 各 agent 只写自己块不读彼此 + 🚪 Merge Gate（合一个焊一个，verify 真跑通才 merge） |

并在生成的 `CLAUDE.md` 末尾补一句并行纪律：「多 agent 并行同一里程碑时，先在 `BOARD.md` 认领再开工；子 agent 只写自己的块、不读不改别人的块；产出过 Merge Gate（verify 真跑通 + diff review）才进 `main`。」方法论全文见 https://github.com/libaoming/harness-kit/blob/main/docs/parallel-agents.md 。

### 第 2 步 · 创建文档桩（PRD/SPEC/architecture）
这三个是项目专属、必须文档先行、不能用通用模板填实。只创建**带章节标题的桩**（模板 `templates/PRD_stub.md` / `SPEC_stub.md` / `architecture_stub.md`），正文留 `> [!TODO]`，提醒用户先讨论再写。

### 第 2b 步 · 未知面试（填 PRD/SPEC 之前，源自 Thariq《A Field Guide to Fable: Finding Your Unknowns》）
文档先行的质量取决于用户澄清了多少「未知」。填 PRD/SPEC 前跑一轮：
1. **blindspot pass**：结合项目定位，主动列出用户可能的 unknown unknowns（没考虑到的坑/不知道「好」长什么样的维度）并讲给他听；
2. **一次一题面试**：就模糊/歧义处提问，**优先问「答案会改变架构」的**（数据模型、边界、集成点、验收口径）；
3. **要参考**：用户说不清想要什么时，请他指一个参考——**最好的参考是源码**（仓库/文件夹/竞品实现），别让他用文字硬描述。
面试产出直接填进 PRD/SPEC；没问出来的未知按「已知的未知」记进 STATUS.md 踩坑清单候补。
**评审载体用 Claude Artifacts（用户 2026-07-04 定）**：PRD/SPEC/architecture/ADR 类文档写完或大改后，渲染一个 Artifact 评审页给用户看——**最可能变动的决策置顶**（带选项 + ★推荐 + 回填锚点，用户回「1A 2B」式一句话拍板），盲区发现次之，文档速览沉底，机械性内容不展开。md 文件仍是单一事实源，Artifact 只是评审视图；拍板后回填 md。

### 第 3 步 · 报告 + 引导文档先行
scaffold 完成后输出：
- 生成的文件树
- **明确告知：代码还不能开始写**——L2 要求 PRD/SPEC/architecture 文档先行写完才动代码
- 引导用户："要现在做一轮未知面试、然后一起填 PRD 吗？"（第 2b 步）

## 注意事项
- 目标目录若已有同名文件，**先确认再覆盖**，不要静默覆盖用户已有内容
- `{PROJECT}-ops.md` 子 agent 默认 **ECS/生产只读**（参考电话/微信项目铁律），若项目无远程部署可在生成后删掉对应段
- 不替用户 `git init` / `git push`，除非用户明确要求
- scaffold 后**不要急着写代码**——L2 的"文档先行"是硬规矩
