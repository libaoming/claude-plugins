---
description: 输出当前 harness 项目的进度表（features.json 统计 + 当前切片 + STATUS 新鲜度）
---

对当前工作目录（或 $ARGUMENTS 指定的目录）做一次 harness 进度速查，**只读不改**：

1. 读 `features.json`：按 status 统计（passing / in_progress / failing / pending），按 slice 分组列出每个 feature 的 id、status、verify 类型
2. 找出当前应做的 feature（第一个非 passing 的），给出它的 verify 标准
3. 看 `STATUS.md` 最后更新时间和「下次入口」一节
4. 检查有没有 status=in_progress 超过 1 个（违反线性推进）或 verify 为空却离开 pending 的 feature（违反 verifier 闸门），有就标 ⚠️

输出一张紧凑的进度表 + 一句「下一步」。如果当前目录没有 features.json，直接说这不是 harness 项目，并提示可用 `/harness-kit:harness-init` 初始化。
