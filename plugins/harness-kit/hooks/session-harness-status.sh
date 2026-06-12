#!/bin/bash
# SessionStart hook: 在 harness 项目里开会话时注入一行进度摘要。
# 非 harness 目录零输出；任何异常都静默退出 —— 此脚本跑在用户每个会话里，绝不允许报错或拖慢。
set -u
exec 2>/dev/null

command -v jq >/dev/null || exit 0

input=$(cat) || exit 0
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty') || exit 0
[ -n "$cwd" ] && [ -d "$cwd" ] || exit 0

fj="$cwd/features.json"
st="$cwd/STATUS.md"
[ -f "$fj" ] && [ -f "$st" ] || exit 0

# 不是 harness 的 features.json（缺 features 数组）也静默跳过
counts=$(jq -r '
  if (.features | type) == "array" then
    [
      ([.features[] | select(.status == "passing")] | length),
      ([.features[] | select(.status != "passing")] | length),
      (.features | length),
      ((first(.features[] | select(.status != "passing")) // {}) .id // "无（全部 passing）"),
      (.milestone // "?")
    ] | @tsv
  else empty end' "$fj") || exit 0
[ -n "$counts" ] || exit 0

IFS=$'\t' read -r passing rest total next_id milestone <<< "$counts"

# STATUS.md 新鲜度（天）
if stat -f %m "$st" >/dev/null 2>&1; then
  mtime=$(stat -f %m "$st")           # macOS
else
  mtime=$(stat -c %Y "$st") || exit 0 # Linux
fi
days=$(( ($(date +%s) - mtime) / 86400 ))
case $days in
  0) fresh="今天更新过" ;;
  1) fresh="1 天前更新" ;;
  *) fresh="${days} 天前更新（注意可能已过期）" ;;
esac

ctx="⚙️ harness 项目进度（${milestone}）：${passing}/${total} passing，当前应做 ${next_id}；STATUS.md ${fresh}。开工前先读 STATUS.md，verify 真跑通才能改 passing。"

jq -cn --arg ctx "$ctx" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
exit 0
