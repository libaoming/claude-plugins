#!/usr/bin/env bash
# record-evidence.sh — verify 影像凭据录制器（harness-kit L2）
#
# 用途：把一次 verify 的「实跑行为」录成视频/GIF 落档，作为 features.json 里
#       verify.evidence 指向的凭据。治「verify 说过了，但没人看得见它跑过什么」。
#
# 用法：
#   ./record-evidence.sh start <feature-id> [url]     # 开录（不传 url 用当前页）
#   ./record-evidence.sh stop  <feature-id> [--gif]   # 停录并落档，--gif 额外转 GIF
#   ./record-evidence.sh path  <feature-id>           # 打印该 feature 的凭据路径
#
# 输出（可判定标量，供 verify 命令直接吃）：
#   EVIDENCE: evidence/<feature-id>.webm
#   EVIDENCE_GIF: evidence/<feature-id>.gif
#   EXIT:0
#
# 依赖：agent-browser（必需）、ffmpeg（仅 --gif 需要）
set -euo pipefail

EVIDENCE_DIR="${EVIDENCE_DIR:-evidence}"
GIF_FPS="${GIF_FPS:-8}"
GIF_WIDTH="${GIF_WIDTH:-960}"

die() { echo "ERROR: $*" >&2; echo "EXIT:1" >&2; exit 1; }

command -v agent-browser >/dev/null 2>&1 || die "agent-browser 未安装（brew install agent-browser）"

cmd="${1:-}"; fid="${2:-}"
[ -n "$cmd" ] || die "用法：$0 start|stop|path <feature-id> [url|--gif]"
[ -n "$fid" ] || die "缺 feature-id（对应 features.json 的 id）"

webm="$EVIDENCE_DIR/$fid.webm"
gif="$EVIDENCE_DIR/$fid.gif"

case "$cmd" in
  start)
    mkdir -p "$EVIDENCE_DIR"
    url="${3:-}"
    if [ -n "$url" ]; then
      agent-browser record start "$webm" "$url" >/dev/null
    else
      agent-browser record start "$webm" >/dev/null
    fi
    echo "RECORDING: $webm"
    echo "EXIT:0"
    ;;

  stop)
    agent-browser record stop >/dev/null
    # 录制文件由浏览器异步落盘，等它出现（最多 10s）
    for _ in $(seq 1 20); do
      [ -s "$webm" ] && break
      sleep 0.5
    done
    [ -s "$webm" ] || die "录制文件未落盘：$webm"
    echo "EVIDENCE: $webm"
    if [ "${3:-}" = "--gif" ]; then
      command -v ffmpeg >/dev/null 2>&1 || die "--gif 需要 ffmpeg"
      ffmpeg -y -loglevel error -i "$webm" \
        -vf "fps=$GIF_FPS,scale=$GIF_WIDTH:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" \
        "$gif"
      [ -s "$gif" ] || die "GIF 转换失败：$gif"
      echo "EVIDENCE_GIF: $gif"
    fi
    echo "EXIT:0"
    ;;

  path)
    [ -s "$webm" ] && echo "EVIDENCE: $webm" || echo "EVIDENCE: (missing) $webm"
    [ -s "$gif" ] && echo "EVIDENCE_GIF: $gif"
    [ -s "$webm" ] && echo "EXIT:0" || { echo "EXIT:1"; exit 1; }
    ;;

  *)
    die "未知子命令：$cmd（start|stop|path）"
    ;;
esac
