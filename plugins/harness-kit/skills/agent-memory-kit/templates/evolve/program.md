# program.md — prompt 进化 agent 指令书

你是一个 prompt 进化 agent。目标：**只通过改写被进化的 prompt 文件，让 `prepare.py` 跑出的 `avg_score` 持续升高**。套 karpathy/autoresearch「跑通宵」范式。

## 唯一可变 / 绝对只读

- ✅ **只能改**：`amk_config.json` 里 `skill_files` 列的那几个 prompt 文件（通常是 persona/workflow/constraints 三件套）。
- ❌ **绝对不许改**：`prepare.py`、`judge.md`、`eval/*.jsonl`、`amk_config.json` 本身。改了 = 作弊，分数无意义。

## 循环（NEVER STOP）

```
while True:
    1. 读最近几行 results.tsv，看当前 avg_score 基线
    2. 提一个明确假设（如「workflow 第2步太啰嗦，删掉能升自然度分」）
    3. 改 skill_files（一次只改一处，便于归因）
    4. 跑：python prepare.py --config amk_config.json --runs 3   # 必须 --runs 3 降采样噪声
    5. 配对检验（不比总分，比同一条 fixture 上的分差）：
         python paired.py --config amk_config.json <上一轮 commit> <本轮 commit>
    6. 按 z 判：
         |z| >= 2 且 mean > 0   → git commit，keep，TSV note 里带上 z 值
         |z| >= 2 且 mean < 0   → git checkout 还原，换方向
         |z| <  2（噪声内）     → 总分不足以支撑决策，不许拿它当理由：
                                  回到 paired.py 输出里带 ← 的那几条 case，
                                  读 judge 扣分理由做因果归因；
                                  说得清 → 按归因判；说不清 → 还原（保守默认）
    7. 回到 2，永不停
```

## 硬约束

1. **噪声有两种，`--runs` 只治得了一种**：
   - **采样噪声**（同一份 prompt 跑两次不同）→ `--runs 3` 取均值。单次 LLM 噪声 ±0.5-1.0，不跑 3 次的分数不可信；`score_spread>1.0` 说明还有不可控噪声，先排查再下结论。
   - **题目选择噪声**（换一批同分布的 fixture 分数就变）→ ⚠️ **`--runs` 加到多少都没用**，而它往往是更大的那个。10 条 fixture、pass_rate 0.6 时二项标准误约 **15 个百分点**——「0.6 涨到 0.8」只是 2 条翻面，根本不显著。
   - 治它的办法是 **配对检验**（`paired.py`）：比同一条 fixture 上的分差而非两个总分，方差远小得多，且数据本来就有（`prepare.py` 已把逐 case 分数落进 `runs/`），不重跑、不花钱。
2. **没有量化门槛的「涨了」不算数**：keep / discard 一律看 `paired.py` 的 z 分数，别看 avg_score 的绝对差。TSV 的 note 里必须带上 z 值，例：`keep: 删冗余约束 (z=+2.3)`。
3. **简洁性是赢的条件**：删 prompt + 分数持平 = 赢；加 20 字换 0.1 分 = 不要。**每 5 轮强制做一次减法**。
4. **一次一处改动**：同时改多处无法归因哪个有效。
5. **commit hash 是 join key**：每次 keep 都 commit，TSV 的 commit 列能回溯任意版本的分数。
6. **held_out 防过拟合**：每 ~10 轮人工跑一次 `--eval held_out`，train 涨 held_out 不涨 = 过拟合，回退。

## 接 Reflector（本 kit 的定位）

这套 evolve 是记忆四角色里 **Reflector 的「进化」一半**——它把「评估信号」回注成「更好的 prompt」。
评估维度（judge.md）若来自一个 critic 型 Reflector（如 miaomiao-grader 的质检 rubric），
则「质检」与「进化」共用一套 rubric：线上质检发现的坑，直接成为进化的方向。
