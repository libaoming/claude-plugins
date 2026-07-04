# SPEC — {{PROJECT}}

> [!TODO] LLM-native 技术规范：用结构化表格 / 枚举 / JSON schema + 显式约束 + 反模式，而非散文。简单项目可精简但不可省。
> [!TODO] 写作原则——**记决策，不记文件路径**：实现决策落在「模块 / 接口 / schema / API 契约」层面，**禁写具体文件路径或代码片段**（会随重构过时）。**例外**：当原型片段比散文更精确时（状态机、reducer、schema、类型形状），可内联，但只保留与决策相关的部分，不贴完整可运行 demo，并标注来源。
> **Anthropic self-contained 三要件**（code.claude.com/docs/en/best-practices）：① 点名涉及的模块与接口（让执行者知道读哪里；决策本身不绑具体路径，与上条一致）② 写明 out of scope ③ **以端到端验证步骤收尾**。「把 spec 写精确的时间回报 > 盯实现的时间。」

## 数据模型 / Schema
> [!TODO]

## 接口 / 协议
> [!TODO]（端点、字段、鉴权、错误码）

## 关键约束
> [!TODO]（必须遵守的硬规则）

## 反模式
> [!TODO]（明确禁止的写法 + 原因）

## 切片关联 — Related Context（每切片开工前填）
> [!TODO] 来自 OpenSpec 实践，让新 session / subagent 秒判"读哪些、不读哪些"，对治 context 膨胀。每个切片填：
> - **Related**：关联的 SPEC 章节 / 代码目录 / 文档（对应 features.json 的 `related`）
> - **Affected behavior**：这个切片影响哪些行为
> - **Out of scope**：明确不碰什么（防 AI 联调时自动复刻隐性功能 → 见踩坑：隐性功能复刻陷阱）

## 端到端验证步骤（收尾必填 · spec 的最后一节）
> [!TODO] Anthropic 硬规矩：spec 以可执行的端到端验证收尾——一条命令/一个脚本/一组步骤，跑完输出 pass/fail，不是给人读的散文验收。这一节直接喂 features.json 的 `verify` 字段。
