# BOARD — {{MILESTONE}} 并行状态板

> **仅在「多个子 agent 并行干同一里程碑」时启用**；单线接力用 `STATUS.md` 就够，别为并行而并行（方法论见 https://github.com/libaoming/harness-kit/blob/main/docs/parallel-agents.md ）。
>
> 🌟 **星型规则**：每个并发子 agent **只写自己认领的块**，**不读、不改别人的块**。信息单向汇聚到本板 + 主线，agent 之间不横向通信。主线（或人 / grader）负责 merge。
>
> 这块板是 steipete 那条「8 个 subagent 各写状态到一个 markdown 文件，我每 5 分钟 merge」的工程化版：板替代了 agent 间相互喊话，merge gate 替代了「谁说完成就算完成」。

---

## 1. 认领表（谁在干什么 · 防撞车）

> 开工前先在这里认领一行，再去自己的 worktree 动手。一个 feature 同一时刻只允许一个 agent 认领。

| feature | 认领 agent | worktree | 状态 | 最后更新 |
|---|---|---|---|---|
| F01_xxx | agent-1 | `wt-F01` | producing | {{DATE}} |
| F02_xxx | agent-2 | `wt-F02` | verifying | {{DATE}} |
| … | … | … | … | … |

---

## 2. 各 agent 工作块（子 agent 写自己这块，主线只读不改）

### F01_xxx · agent-1
- **状态**：producing → verifying → done（对齐 `features.json` 的 status）
- **worktree**：`wt-F01`（隔离改动，避免与他人改同一文件冲突）
- **产出**：（一句话：改了哪个文件的哪个函数 / 加了什么）
- **diff 位置**：`git diff main..wt-F01`（主线据此 review，不必进子 agent 的 context）
- **blocker**：无 ／ 等 F02 的 schema 定稿（**写依赖即可，不要去读对方的块**——依赖由主线在 merge 时裁决）

### F02_xxx · agent-2
- **状态**：…
- **worktree**：`wt-F02`
- **产出**：…
- **diff 位置**：`git diff main..wt-F02`
- **blocker**：…

### …（每个并发 feature 一块，照上面复制）

---

## 3. 🚪 Merge Gate（汇聚验收门 · 合一个焊一个）

> N 路并行产出**不自动合并**，每一路过这道门才进 `main`。这道门是 steipete 的「I review the diffs / I just merge」——**验收者是人，或一个 grader 子 agent 初审 + 人复核**。

| feature | verify 真跑通? | diff review? | 决定 |
|---|---|---|---|
| F01_xxx | ☐ | ☐ | ☐ merge ／ ☐ 打回 producing |
| F02_xxx | ☐ | ☐ | ☐ merge ／ ☐ 打回 producing |

- **验收人**：人工 review ／ grader 初审标红 + 人只看标红（角色分工见 https://github.com/libaoming/harness-kit/blob/main/docs/parallel-agents.md §三个角色）。
- **打回规则**：verify 没真跑通的，状态退回 `producing`，**不准 merge**（沿用 L2「verify 真跑通才 passing」）。
- **merge 完一个**：更新 `features.json` 该 feature 为 `passing` → 删掉本板对应块 → 删除其 worktree（`git worktree remove wt-F01`）。

---

## 4. 与 STATUS.md 的分工

- `STATUS.md` = **接力视角**（单一、给下一个会话 / 人看「我在哪、下一步」），收尾必更新。
- `BOARD.md` = **并行视角**（N 个 agent 此刻各自到哪），并行期间存在，全部 merge 完即清空或归档。
- 两者正交：并行跑完、产出都 merge 回 `main` 后，把结论一句话写回 `STATUS.md`，BOARD 清空。
