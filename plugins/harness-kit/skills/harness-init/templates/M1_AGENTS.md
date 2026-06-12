# {{MILESTONE}} Session Kickoff（开新会话先读这份）

> 接班说明：不靠任何人讲背景，10 分钟内选到正确的下一件事干。
> 依据：Anthropic "Effective Harnesses for Long-Running Agents"。

## 0. 一句话定位
{{POSITIONING}}

## 1. Session 启动 5 步
1. `cat {{MILESTONE}}/PROGRESS.md` → 看 active_feature / blockers / next_candidates
2. 读 `../STATUS.md` → 一句话状态 + 踩坑
3. `bash {{MILESTONE}}/init.sh` → 环境全绿才开工
4. 按"选 feature 算法"挑下一件事
5. 动手 → 收尾更新 PROGRESS.md + STATUS.md

## 2. 选 feature 算法
1. 优先 `status=failing` 且 `blocking=[]` 的最低编号 feature
2. 没有则取 `pending` 且依赖已 passing 的
3. 同一 slice 内做完再进下一 slice（线性切片）

## 3. 4 条硬规矩
1. **fixture 先于代码**：verify 引用的 fixture 不存在就先造，不许 mock
2. **verify 真跑通才改 passing**：单测过只到 in_progress
3. **不跳 slice**：当前 slice 的 exit_criteria 没达成不开下一个
4. **收尾必更新 PROGRESS.md + STATUS.md**

## 4. commit 规范
`{feat|fix|refactor|docs}(feature_id): 描述`

## 5. 反模式
过早宣布胜利 / 一次性大包大揽 / 环境不可复现 / 缺端到端验证 → 对应修法见项目 CLAUDE.md L2。
