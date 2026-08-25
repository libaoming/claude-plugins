#!/usr/bin/env python3
"""配对检验 — 判断两轮之间的分差是不是噪声。

为什么需要它
------------
`--runs N` 降的是**采样噪声**（同一份 prompt 跑两次结果不同）。但评测里还有第二种
噪声：**题目选择噪声**——换一批同分布的 fixture，分数就会变，而它往往是更大的那个。
`--runs` 对它无能为力，加多少轮都没用。

fixture 通常只有 10 条左右。10 条、pass_rate 0.6 时，二项标准误约 15 个百分点，
意味着「pass_rate 从 0.6 涨到 0.8」（只有 2 条 fixture 翻面）根本不显著。
只比两个总分，绝大多数真实改动都读不出来。

配对检验换个比法：不比两个总分，比**同一条 fixture 上的分差**。两版 prompt 在同一条
case 上高度相关，配对后方差远小于总分之差——而且数据本来就有（prepare.py 已把逐
case 分数落进 runs/），不需要重跑、不额外花钱。

用法
----
    paired.py --config amk_config.json --list          列出已存档的轮次
    paired.py --config amk_config.json <A> <B>         比较两轮
    paired.py --config amk_config.json <A> <B> --eval held_out
    paired.py --dir path/to/runs <A> <B>               直接指定存档目录

存档目录：prepare.py 写在 `project_root/runs/`。传 --config 会自动定位到那里；
不传则用 --dir（默认当前目录下的 ./runs）。

判读
----
    |z| >= 2   脱离噪声，可据此 keep / discard
    |z| <  2   噪声内 —— 总分不足以支撑决策，回到逐 case 看带 ← 的那几条做因果归因
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


def load_run(path: Path) -> dict[str, float]:
    """读一份 per-case JSONL，返回 {case_id: 该 case 在各 run 上的均分}。

    prepare.py --runs N 会为同一个 case 写 N 行；这里先在 case 内取均值，
    把采样噪声压掉，再进入配对（配对处理的是题目选择噪声）。
    """
    buckets: dict[str, list[float]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        buckets[row["case_id"]].append(float(row["score"]))
    return {cid: sum(v) / len(v) for cid, v in buckets.items()}


def paired_stats(a: dict[str, float], b: dict[str, float]) -> dict:
    common = sorted(set(a) & set(b))
    diffs = [b[c] - a[c] for c in common]
    n = len(diffs)
    if n == 0:
        return {"n": 0}
    mean = sum(diffs) / n
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1) if n > 1 else 0.0
    se = math.sqrt(var / n) if n > 1 else 0.0
    if se:
        z = mean / se
    else:
        z = math.inf if mean > 0 else (-math.inf if mean < 0 else 0.0)
    return {
        "n": n, "common": common, "mean": mean, "se": se, "z": z,
        "improved": sum(1 for d in diffs if d > 0),
        "worsened": sum(1 for d in diffs if d < 0),
        "unchanged": sum(1 for d in diffs if d == 0),
    }


def resolve(runs_dir: Path, tag: str, eval_set: str) -> Path:
    """tag 可以是 commit hash，也可以是完整文件名。"""
    for cand in (runs_dir / f"{tag}-{eval_set}.jsonl", runs_dir / tag, Path(tag)):
        if cand.exists():
            return cand
    raise FileNotFoundError(f"找不到 {tag}（在 {runs_dir} 下找 {tag}-{eval_set}.jsonl）")


def cmd_compare(runs_dir: Path, tag_a: str, tag_b: str, eval_set: str) -> int:
    try:
        pa, pb = resolve(runs_dir, tag_a, eval_set), resolve(runs_dir, tag_b, eval_set)
    except FileNotFoundError as e:
        print(f"[错误] {e}", file=sys.stderr)
        return 1
    a, b = load_run(pa), load_run(pb)
    st = paired_stats(a, b)
    if st["n"] == 0:
        print("[错误] 两轮没有共同的 case，无法配对。", file=sys.stderr)
        return 1

    print(f"配对检验  {tag_a} → {tag_b}   (eval_set={eval_set})")
    print("=" * 64)
    print(f"{'case':<22}{tag_a[:9]:>10}{tag_b[:9]:>10}{'Δ':>9}")
    print("-" * 64)
    for c in st["common"]:
        d = b[c] - a[c]
        print(f"{c:<22}{a[c]:>10.1f}{b[c]:>10.1f}{d:>+9.1f}{'  ←' if abs(d) > 1e-9 else ''}")
    print("-" * 64)
    print(f"共同 case:            {st['n']}")
    print(f"变好 / 变差 / 持平:   {st['improved']} / {st['worsened']} / {st['unchanged']}")
    print(f"平均分差:             {st['mean']:+.3f}")
    print(f"配对标准误:           {st['se']:.3f}")
    print(f"z 分数:               {st['z']:+.2f}")
    print()
    if abs(st["z"]) >= 2:
        verdict = "真提升" if st["mean"] > 0 else "真下降"
        print(f"判定：脱离噪声（|z| ≥ 2）→ {verdict}，可据此 keep / discard。")
    else:
        print("判定：⚠️ 噪声内（|z| < 2）——总分不足以支撑决策。")
        print("      回到上表带 ← 的那几条 case，读 judge 的扣分理由做因果归因：")
        print("      说得清「这条为什么变、是不是这次改动造成的」→ 按归因判；")
        print("      说不清 → discard（保守默认），并在 TSV note 里写明「归因不清」。")
    return 0


def cmd_list(runs_dir: Path) -> int:
    files = sorted(runs_dir.glob("*.jsonl"))
    if not files:
        print(f"{runs_dir} 下还没有存档。跑一次 prepare.py 即可生成。")
        return 0
    print(f"已存档 {len(files)} 轮：")
    for p in files:
        cases = load_run(p)
        avg = sum(cases.values()) / len(cases) if cases else 0.0
        print(f"  {p.stem:<28} {len(cases):>3} cases   avg={avg:.2f}")
    return 0


def _resolve_runs_dir(args) -> Path:
    """--dir 优先；否则从 --config 读 project_root/runs；都没有则 ./runs。"""
    if args.dir:
        return Path(args.dir)
    if args.config:
        cfg_path = Path(args.config)
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        root = cfg.get("project_root") or "."
        base = cfg_path.parent if root == "." else Path(root)
        if not base.is_absolute():
            base = (cfg_path.parent / base).resolve()
        return base / "runs"
    return Path("runs")


def main() -> int:
    ap = argparse.ArgumentParser(description="配对检验：两轮之间的分差是不是噪声")
    ap.add_argument("tags", nargs="*", help="两个 commit hash（或存档文件名）")
    ap.add_argument("--config", help="amk_config.json 路径（据此定位 project_root/runs）")
    ap.add_argument("--dir", help="直接指定存档目录（默认 ./runs）")
    ap.add_argument("--eval", default="train_set", help="eval 集名（默认 train_set）")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    runs_dir = _resolve_runs_dir(args)
    if args.list:
        return cmd_list(runs_dir)
    if len(args.tags) == 2:
        return cmd_compare(runs_dir, args.tags[0], args.tags[1], args.eval)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
