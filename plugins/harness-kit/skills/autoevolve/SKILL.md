---
name: autoevolve
description: 给任意 prompt/skill/agent 人格文件挂「自动进化环」：fixture → agent 跑 → LLM judge 评分 → TSV 记账 → agent 自己改 prompt 再跑，分数不涨就回退（karpathy autoresearch「跑通宵」范式）。当用户说"给这套 prompt 做自动进化/挂 autoevolve/让分数自己涨/prompt 闭环优化/eval harness"时使用。落地物：7 文件骨架（program.md 指令书 + judge.md rubric + prepare.py 评测器 + paired.py 配对检验 + train/held_out fixtures + results.tsv 记账）。
---

# Autoevolve 挂载 Agent

给目标项目落一套 prompt 自动进化骨架。核心五要素：**单可变文件 + 固定预算 + 单一标量 + TSV 记账 + NEVER STOP**。

## 执行流程

### 第 0 步 · 确认四件事
1. **被进化的对象**：哪几个 prompt 文件？（即 config 里的 `skill_files`，通常是 persona/workflow/constraints 三件套——必须是「唯一可变」的明确清单）
2. **怎么算好**：judge 的评分维度从哪来？（最好复用项目已有的质检 rubric——「质检」与「进化」共用一套标尺，线上发现的坑直接成为进化方向）
3. ⭐ **维度分流（建 fixture 之前先做，别跳）**：把第 2 步列出的每一条判据打上标签——**「必须一致」还是「允许方差」**。只有「必须一致」的进 judge rubric、进总分；「允许方差」的最多人工抽检，**不进 `results.tsv` 的总分**。
   - 判据：问「同一个输入，agent 这次这么答、下次那么答，算不算 bug？」——不算 → 允许方差。
   - 典型「必须一致」：结构化字段抽对没有、用户指定的状态/参数有没有被落实、该拒绝的有没有拒绝、格式契约。
   - 典型「允许方差」：措辞与语气、组织信息的顺序、开放式建议的具体内容、创意性输出。
   - **为什么必须先分流**：在允许方差的维度上堆 eval，分数会左右横跳，产出的不是信号是噪音——它既**掩盖真正该测维度的进退**（总分被稀释），又会把进化 agent 往**过拟合**方向拽（为了让那个分好看而不断加约束，最后 prompt 越写越长、越写越脆）。
   - 出处：Linear 工程负责人 Jacob Shumway，「**evals are most successful when you're ensuring consistency somewhere that consistency is important. But consistency is not always important for agents.** ... you really don't want to have too many evals around that, because then it's just false signals.」
4. **fixture 从哪来**：10 个左右训练 case + 5 个 agent 不可见的 held_out 对照 case（**只为第 3 步分流出的「必须一致」维度造**）

### 第 1 步 · 落 7 文件骨架
模板在本 plugin 内 `../agent-memory-kit/templates/evolve/`（同 plugin 共享一份，先用本 skill 的 base 目录拼出绝对路径），复制到 `{dir}/memory/evolve/`（或用户指定目录）：

| 文件 | 作用 | 谁能改 |
|---|---|---|
| `program.md` | 进化 agent 指令书（循环 + 硬约束） | 人 |
| `judge.md` | LLM judge rubric | 人（agent 绝对不许改） |
| `prepare.py` | 评测器：跑 fixture → judge 打分 → 写 TSV + 逐 case 落 `runs/` | 人（agent 只读） |
| `paired.py` | 配对检验：读 `runs/` 判两轮分差是不是噪声 | 人（agent 只读，但每轮要跑） |
| `amk_config.example.json` | 复制为 `amk_config.json`，填 `skill_files` / fixture 路径 | 人 |
| `eval/train_set.jsonl` | agent 可见的训练 fixture（替换为项目自己的 case） | 人 |
| `eval/held_out.jsonl` | agent **不可见**的对照 fixture（防过拟合） | 人 |

`results.tsv`、`run.log` 与 `runs/*.jsonl`（逐 case 存档）由运行时生成，提醒用户加进 `.gitignore`。

### 第 2 步 · 跑基线
```bash
python3 prepare.py --config amk_config.json --runs 3
```
基线分进 TSV 第一行。**没有基线分，后面所有进化都无从归因。**

### 第 3 步 · 交付报告
输出骨架文件树 + 基线分 + 启动进化环的方式（把 `program.md` 喂给一个长跑 agent 会话）。

## 硬约束（写进交付报告，逐条给用户）
1. **噪声有两种，`--runs` 只治得了一种**：
   - **采样噪声**（同一份 prompt 跑两次不同）→ `--runs 3` 取均值。单次 LLM 噪声 ±0.5-1.0，不跑 3 次的分数不可信。
   - **题目选择噪声**（换一批同分布 fixture 分数就变）→ ⚠️ **`--runs` 加到多少都没用**，而它往往是更大的那个。**10 条 fixture、pass_rate 0.6 时二项标准误约 15 个百分点**——「0.6 涨到 0.8」只是 2 条翻面，根本不显著。
2. **keep / discard 看 z 不看绝对分差**：每轮跑 `paired.py <上一轮 commit> <本轮 commit>`，`|z| >= 2` 才算脱离噪声。噪声内时**不许拿总分当理由**，回到逐 case 读 judge 扣分理由做因果归因；说不清就还原。TSV note 里带上 z 值。
3. **一次一处改动**：同时改多处无法归因
4. **简洁性是赢的条件**：删 prompt 分数持平 = 赢；每 5 轮强制做一次减法
5. **commit hash 是 join key**：每次 keep 都 commit，TSV 可回溯任意版本；`runs/` 里的逐 case 存档也按 commit 命名，两边对得上
6. **held_out 防过拟合**：每 ~10 轮人工跑一次，train 涨 held_out 不涨 = 过拟合，回退
7. **只对「必须一致」的维度计分**：第 0 步分流为「允许方差」的维度不进 judge rubric、不进总分。这条与第 6 条是两道正交的筛子——**held_out 筛的是「有没有过拟合到训练集」，本条筛的是「这个维度到底该不该被测」**。分数在允许方差的维度上波动，看起来像质量变化，其实是噪音

## 不要做的事（实战教训，原样转告用户）
- ❌ 让 agent 自己跑 held-out
- ❌ 让 agent 改 prepare.py / judge.md / eval/*.jsonl / config 本身（改了 = 作弊，分数无意义）
- ❌ 在被进化的 prompt 里写"请按 judge 标准回复"（对着标尺作弊）
- ❌ 用单点高分定胜负——看 TSV 趋势
- ❌ **拿没过 z 检验的分差当 keep / discard 的理由**——fixture 只有 10 条时，绝大多数「涨了 0.2」都在噪声里；这样跑出来的进化环是在追噪声，而且因为记录看着在涨，它不会自己暴露
- ❌ judge 与被测 agent 用同一个模型档位（自相关偏差；judge 用更强档位，且每 ~200 轮人工抽检 5 个 case）
