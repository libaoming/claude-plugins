"""harvest.py — 把线上失败 trace 收成候选 fixture，经人改写后再晋升进评测集。

对应 prepare.py 的上游：prepare.py 只负责「拿 fixture 打分」，fixture 从哪来原本靠人手写。
本脚本补上「线上质检发现的坑 → 进化方向」这一环（见 program.md「接 Reflector」）。

两道闸，都由人来过：
    1. harvest 只写 eval/candidates.jsonl，从不碰 train_set / held_out
    2. promote 要求 expected 已被人改写（不再以 TODO 开头），否则拒绝

失败 trace 的格式（JSONL，每行一段对话，通常来自 critic 型 Reflector 或人工标注）：
    {"id": "可选", "stage": "可选", "category": "可选（失败归类）",
     "messages": [{"role": "user", ...}, ..., {"role": "assistant", "content": "坏回复"}],
     "verdict": {"score": 3, "pass": false, "reasons": "..."}}
判定为失败：verdict.pass 为 false；没有 pass 时 score < 7。没有 verdict 的不猜，计入 unjudged。

用法：
    python3 harvest.py --config amk_config.json --traces failures.jsonl   # 收候选
    python3 harvest.py --config amk_config.json --list                    # 看候选池
    python3 harvest.py --config amk_config.json --promote ID --to train_set|held_out
    python3 harvest.py --config amk_config.json --reject ID               # 丢弃，记进 rejected.jsonl，以后不再收
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

TODO_PREFIX = "TODO"
PASS_THRESHOLD = 7  # 与 prepare.py / judge.md 的 score>=7 记 pass 保持一致
TARGETS = ("train_set", "held_out")


def load_eval_dir(config_path: str) -> Path:
    cfg_path = Path(config_path).expanduser().resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    root = cfg.get("project_root")
    root = Path(root).expanduser().resolve() if root else cfg_path.parent
    return root / cfg.get("eval_dir", "eval")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    os.replace(tmp, path)


def append_jsonl(path: Path, rows: list[dict]) -> None:
    # 手改过的文件末尾可能没有换行，直接追加会把两条 JSON 拼到同一行
    if path.exists() and path.stat().st_size and not path.read_bytes().endswith(b"\n"):
        with path.open("a", encoding="utf-8") as f:
            f.write("\n")
    with path.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def conv_key(messages: list[dict]) -> str:
    norm = [{"role": m.get("role"), "content": m.get("content")} for m in messages]
    return hashlib.sha1(json.dumps(norm, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def is_failed(trace: dict) -> bool | None:
    """True=失败 / False=通过 / None=没有判定。pass 只认布尔值，否则看 score。"""
    v = trace.get("verdict")
    if not isinstance(v, dict):
        return None
    if isinstance(v.get("pass"), bool):
        return not v["pass"]
    try:
        return float(v["score"]) < PASS_THRESHOLD
    except (KeyError, TypeError, ValueError):
        return None


def is_draft(expected) -> bool:
    """expected 还没被人改写：空、全空白、或以 TODO 开头（不分大小写）。"""
    text = str(expected or "").strip()
    return not text or text.upper().startswith(TODO_PREFIX)


def split_conversation(messages) -> tuple[list[dict], str] | None:
    """去掉末尾的坏回复，返回 (以 user 结尾的对话, 坏回复)；结构不合法返回 None。"""
    if not isinstance(messages, list) or not all(
            isinstance(m, dict) and isinstance(m.get("content"), str) for m in messages):
        return None
    messages = list(messages)
    bad_response = messages.pop()["content"] if messages and messages[-1].get("role") == "assistant" else ""
    if not messages or messages[-1].get("role") != "user":
        return None
    return messages, bad_response


def harvest(eval_dir: Path, traces_path: Path) -> int:
    cand_path = eval_dir / "candidates.jsonl"
    if not eval_dir.is_dir():
        print(f"ERROR: eval 目录不存在: {eval_dir}", file=sys.stderr)
        return 1
    seen = {conv_key(c["messages"]) for name in (*TARGETS, "candidates", "rejected")
            for c in read_jsonl(eval_dir / f"{name}.jsonl")}
    counts = dict.fromkeys(("read", "failed", "passed", "unjudged", "invalid", "dup", "new"), 0)
    by_category: dict[str, int] = {}
    new_rows: list[dict] = []
    today = datetime.date.today().isoformat()

    for raw in traces_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        counts["read"] += 1
        try:
            trace = json.loads(raw)
        except json.JSONDecodeError:
            trace = None
        split = split_conversation(trace.get("messages")) if isinstance(trace, dict) else None
        if split is None:
            counts["invalid"] += 1
            continue
        messages, bad_response = split
        failed = is_failed(trace)
        if failed is None:
            counts["unjudged"] += 1
            continue
        if not failed:
            counts["passed"] += 1
            continue
        counts["failed"] += 1
        key = conv_key(messages)
        if key in seen:
            counts["dup"] += 1
            continue
        seen.add(key)

        reasons = str(trace["verdict"].get("reasons") or "")
        category = trace.get("category") or "未归类"
        by_category[category] = by_category.get(category, 0) + 1
        new_rows.append({
            "id": f"H-{today}-{key[:8]}",
            "stage": trace.get("stage", "线上失败"),
            "messages": messages,
            "expected": f"{TODO_PREFIX}(人写)：失败原因={reasons}。改写成「应该怎么做」的正向描述后才能 promote",
            "source": {"trace_id": trace.get("id"), "category": category,
                       "reasons": reasons, "bad_response": bad_response},
        })
        counts["new"] += 1

    if new_rows:
        append_jsonl(cand_path, new_rows)
    print(" ".join(f"{k}={v}" for k, v in counts.items()))
    for cat, n in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {n}")
    print(f"candidates: {cand_path}")
    return 0


def list_candidates(eval_dir: Path) -> int:
    rows = read_jsonl(eval_dir / "candidates.jsonl")
    for c in rows:
        state = "待改写" if is_draft(c.get("expected")) else "可晋升"
        src = c.get("source") or {}
        print(f"{c.get('id')}\t{state}\t{src.get('category') or ''}\t{str(src.get('reasons') or '')[:60]}")
    print(f"total={len(rows)}")
    return 0


def promote(eval_dir: Path, case_id: str, target: str) -> int:
    cand_path = eval_dir / "candidates.jsonl"
    rows = read_jsonl(cand_path)
    hit = [c for c in rows if c.get("id") == case_id]
    if not hit:
        print(f"NOT_FOUND {case_id}")
        return 1
    case = hit[0]
    if target != "rejected" and is_draft(case.get("expected")):
        print(f"REFUSED {case_id}: expected 还是 TODO 草稿或为空，先把它改写成「应该怎么做」")
        return 2
    # 先追加再移出候选池；中途中断后重跑时，目标集里已有同 id 就不再追加，避免写两次
    target_path = eval_dir / f"{target}.jsonl"
    if all(c.get("id") != case_id for c in read_jsonl(target_path)):
        append_jsonl(target_path, [case])
    write_jsonl(cand_path, [c for c in rows if c.get("id") != case_id])
    print(f"{'REJECTED' if target == 'rejected' else 'PROMOTED'} {case_id} -> {target}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="失败 trace → 候选 fixture → 人工晋升")
    p.add_argument("--config", required=True, help="amk_config.json 路径")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--traces", help="失败 trace 的 JSONL 文件")
    g.add_argument("--list", action="store_true", help="列出候选池")
    g.add_argument("--promote", metavar="ID", help="把一个候选晋升进评测集")
    g.add_argument("--reject", metavar="ID", help="丢弃一个候选（记进 rejected.jsonl，以后同一段对话不再收）")
    p.add_argument("--to", choices=TARGETS, help="--promote 的目标集")
    args = p.parse_args()

    eval_dir = load_eval_dir(args.config)
    if args.traces:
        return harvest(eval_dir, Path(args.traces).expanduser())
    if args.list:
        return list_candidates(eval_dir)
    if args.reject:
        return promote(eval_dir, args.reject, "rejected")
    if not args.to:
        p.error("--promote 需要 --to train_set|held_out")
    return promote(eval_dir, args.promote, args.to)


if __name__ == "__main__":
    sys.exit(main())
