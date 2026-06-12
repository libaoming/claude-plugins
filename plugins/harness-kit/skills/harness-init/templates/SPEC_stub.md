# SPEC — {{PROJECT}}

> [!TODO] LLM-native 技术规范：用结构化表格 / 枚举 / JSON schema + 显式约束 + 反模式，而非散文。简单项目可精简但不可省。

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
