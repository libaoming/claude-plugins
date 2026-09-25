"""test_harvest.py — harvest.py 的验收测试（零依赖，python3 test_harvest.py 直接跑）。

验收标准：
1. 只收判定为失败的 trace；没有判定的不猜，单独计数
2. 去掉最后那条坏回复，对话以 user 结尾；坏回复留在 source 里备查
3. 与 train_set / held_out / candidates 里已有的对话去重
4. expected 还是 TODO 草稿时拒绝 promote；改写后才能晋升，并从候选池移除
5. 不写 train_set / held_out，除非走 promote
6. 各项计数加起来等于 read；不合规输入计入 invalid，不崩
7. 丢弃的候选以后不再被收回；promote 中断重跑不会写两次；目标文件末尾缺换行也不会拼行
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARVEST = HERE / "harvest.py"


def sh(cfg: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HARVEST), "--config", str(cfg), *args],
                          capture_output=True, text=True)


def read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    (tmp / "eval").mkdir()
    cfg = tmp / "amk_config.json"
    cfg.write_text(json.dumps({"eval_dir": "eval"}), encoding="utf-8")
    existing = {"id": "T01", "messages": [{"role": "user", "content": "你好"}], "expected": "问关键信息"}
    (tmp / "eval" / "train_set.jsonl").write_text(json.dumps(existing, ensure_ascii=False) + "\n", encoding="utf-8")
    (tmp / "eval" / "held_out.jsonl").write_text("", encoding="utf-8")
    train_before = (tmp / "eval" / "train_set.jsonl").read_text(encoding="utf-8")

    traces = [
        # 失败（pass=false），末尾是坏回复
        {"id": "tr-1", "category": "边界", "messages": [
            {"role": "user", "content": "今天天气怎么样"},
            {"role": "assistant", "content": "今天晴，适合出去玩！"}],
         "verdict": {"score": 3, "pass": False, "reasons": "陪聊天气，没拉回主线"}},
        # 失败（只有 score，没有 pass）
        {"id": "tr-2", "messages": [
            {"role": "user", "content": "浦东有夜班吗"},
            {"role": "assistant", "content": "有的有的"}],
         "verdict": {"score": 5, "reasons": "编造岗位"}},
        # 通过，不收
        {"id": "tr-3", "messages": [{"role": "user", "content": "嗨"}, {"role": "assistant", "content": "您想找哪个区域？"}],
         "verdict": {"score": 9, "pass": True, "reasons": "ok"}},
        # 没有判定，不猜
        {"id": "tr-4", "messages": [{"role": "user", "content": "在吗"}, {"role": "assistant", "content": "在"}]},
        # 与已有 train_set 重复（去掉坏回复后就是「你好」）
        {"id": "tr-5", "messages": [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你好呀"}],
         "verdict": {"score": 2, "pass": False, "reasons": "寒暄空转"}},
        # 和 tr-1 同一段对话（重复失败），只收一次
        {"id": "tr-6", "messages": [
            {"role": "user", "content": "今天天气怎么样"},
            {"role": "assistant", "content": "多云"}],
         "verdict": {"score": 4, "pass": False, "reasons": "陪聊"}},
        # 去掉坏回复后不以 user 结尾，非法
        {"id": "tr-7", "messages": [{"role": "assistant", "content": "欢迎"}],
         "verdict": {"score": 1, "pass": False, "reasons": "x"}},
    ]
    tf = tmp / "failures.jsonl"
    tf.write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in traces) + "\nnot json\n", encoding="utf-8")

    fails: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            fails.append(msg)

    r = sh(cfg, "--traces", str(tf))
    check(r.returncode == 0, f"harvest 退出码 {r.returncode}: {r.stderr}")
    cands = read_jsonl(tmp / "eval" / "candidates.jsonl")
    check(len(cands) == 2, f"候选数应为 2，实为 {len(cands)}")
    check("read=8" in r.stdout and "failed=4" in r.stdout and "new=2" in r.stdout
          and "dup=2" in r.stdout and "unjudged=1" in r.stdout and "invalid=2" in r.stdout,
          f"计数行不对: {r.stdout!r}")
    for c in cands:
        check(c["messages"][-1]["role"] == "user", f"{c['id']} 未以 user 结尾")
        check(c["expected"].startswith("TODO"), f"{c['id']} expected 不是 TODO 草稿")
        check(bool(c["source"].get("bad_response")), f"{c['id']} 没保留坏回复")
    check((tmp / "eval" / "train_set.jsonl").read_text(encoding="utf-8") == train_before, "harvest 动了 train_set")

    # 再跑一次：全部去重，幂等
    r2 = sh(cfg, "--traces", str(tf))
    check("new=0" in r2.stdout, f"重跑应 new=0: {r2.stdout!r}")
    check(len(read_jsonl(tmp / "eval" / "candidates.jsonl")) == 2, "重跑后候选数变了")

    # TODO 未改写 → 拒绝 promote
    cid = cands[0]["id"]
    r3 = sh(cfg, "--promote", cid, "--to", "train_set")
    check(r3.returncode != 0 and "REFUSED" in r3.stdout, f"TODO 草稿应被拒: rc={r3.returncode} {r3.stdout!r}")
    check((tmp / "eval" / "train_set.jsonl").read_text(encoding="utf-8") == train_before, "被拒后 train_set 被改了")

    # 人改写 expected 后 → promote 成功
    cands[0]["expected"] = "应礼貌地把话题拉回找工作主线，不陪聊天气"
    (tmp / "eval" / "candidates.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cands), encoding="utf-8")
    r4 = sh(cfg, "--promote", cid, "--to", "held_out")
    check(r4.returncode == 0 and "PROMOTED" in r4.stdout, f"promote 应成功: {r4.stdout!r} {r4.stderr!r}")
    held = read_jsonl(tmp / "eval" / "held_out.jsonl")
    check(len(held) == 1 and held[0]["id"] == cid, "held_out 未收到晋升的 case")
    check(all(c["id"] != cid for c in read_jsonl(tmp / "eval" / "candidates.jsonl")), "晋升后未从候选池移除")

    # 不存在的 id / 非法目标
    check(sh(cfg, "--promote", "nope", "--to", "train_set").returncode != 0, "不存在的 id 应失败")
    check(sh(cfg, "--promote", cands[1]["id"], "--to", "candidates").returncode != 0, "--to 只许 train_set/held_out")

    # --list 能跑
    r5 = sh(cfg, "--list")
    check(r5.returncode == 0 and cands[1]["id"] in r5.stdout, f"--list 输出不对: {r5.stdout!r}")

    # 6. 计数守恒
    nums = dict(kv.split("=") for kv in r.stdout.split("\n")[0].split())
    total = sum(int(nums[k]) for k in ("passed", "unjudged", "invalid", "failed"))
    check(total == int(nums["read"]), f"计数不守恒: {nums}")

    # 2. 空白 / 小写 todo / 前导空格 TODO 都算草稿
    c2 = read_jsonl(tmp / "eval" / "candidates.jsonl")[0]
    for bad in ("   ", "", " TODO 写一下", "todo：xx", None):
        c2["expected"] = bad
        (tmp / "eval" / "candidates.jsonl").write_text(json.dumps(c2, ensure_ascii=False) + "\n", encoding="utf-8")
        rr = sh(cfg, "--promote", c2["id"], "--to", "train_set")
        check(rr.returncode != 0 and "REFUSED" in rr.stdout, f"expected={bad!r} 应被拒: {rr.stdout!r}")

    # 3. reject 后重跑 harvest 不再收回
    rj = sh(cfg, "--reject", c2["id"])
    check(rj.returncode == 0 and "REJECTED" in rj.stdout, f"reject 失败: {rj.stdout!r}")
    r6 = sh(cfg, "--traces", str(tf))
    check("new=0" in r6.stdout, f"丢弃后重跑应 new=0: {r6.stdout!r}")

    # 1. 目标文件末尾缺换行
    tp = tmp / "eval" / "train_set.jsonl"
    tp.write_text(tp.read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8")
    f2 = tmp / "f2.jsonl"
    f2.write_text(json.dumps({"id": "n", "messages": [{"role": "user", "content": "新问题"}],
                              "verdict": {"score": "6.5", "reasons": None}}, ensure_ascii=False) + "\n", encoding="utf-8")
    r7 = sh(cfg, "--traces", str(f2))
    check("new=1" in r7.stdout, f"score='6.5' 应算失败: {r7.stdout!r} {r7.stderr!r}")
    check(sh(cfg, "--list").returncode == 0, "reasons=None 时 --list 崩了")
    c3 = read_jsonl(tmp / "eval" / "candidates.jsonl")[-1]
    c3["expected"] = "应该这样答"
    (tmp / "eval" / "candidates.jsonl").write_text(json.dumps(c3, ensure_ascii=False) + "\n", encoding="utf-8")
    # 7. 模拟中断：目标集已有同 id，但候选池里还在
    append_line = json.dumps(c3, ensure_ascii=False)
    r8 = sh(cfg, "--promote", c3["id"], "--to", "train_set")
    check(r8.returncode == 0, f"promote 失败: {r8.stdout!r}")
    try:
        rows = read_jsonl(tp)
        check([x["id"] for x in rows].count(c3["id"]) == 1, "目标集里同 id 不是 1 条")
    except json.JSONDecodeError as e:
        check(False, f"缺换行导致拼行: {e}")
    (tmp / "eval" / "candidates.jsonl").write_text(append_line + "\n", encoding="utf-8")
    sh(cfg, "--promote", c3["id"], "--to", "train_set")
    check([x["id"] for x in read_jsonl(tp)].count(c3["id"]) == 1, "中断重跑后写了两次")

    # 5. 不合规输入不崩
    f3 = tmp / "f3.jsonl"
    f3.write_text('{"messages": "字符串", "verdict": {"pass": false}}\n[1,2]\n{"messages": [1], "verdict": {"pass": false}}\n', encoding="utf-8")
    r9 = sh(cfg, "--traces", str(f3))
    check(r9.returncode == 0 and "invalid=3" in r9.stdout, f"不合规输入应计 invalid=3: {r9.stdout!r} {r9.stderr[-200:]!r}")
    cfg2 = tmp / "sub" / "c.json"
    cfg2.parent.mkdir()
    cfg2.write_text("{}", encoding="utf-8")
    r10 = sh(cfg2, "--traces", str(f3))
    check(r10.returncode == 1 and "Traceback" not in r10.stderr, f"eval 目录缺失应干净报错: {r10.stderr[-200:]!r}")

    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
