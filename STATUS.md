# STATUS — claude-plugins

**一句话状态**：harness-kit plugin S1-S5 全部 passing（3 skills + 1 agent + 1 command + 1 hook 全 verify 过），S6 marketplace 发布进行中。

**下次入口**：
1. S6 收尾：GitHub 安装验证 → 归档 `~/.claude/skills/harness-init` → version bump 走 update 流
2. S7（可选）：把各切片「学到的机制」整理成橙研所拆解文章

**踩坑清单**：
- plugin 内不能引用 plugin 外路径（marketplace 安装只复制 plugin 目录）——templates 必须随 skill 走；同 plugin 内跨 skill 相对引用（`../`）安全
- marketplace 安装是复制：装完改源码不生效，开发用 `--plugin-dir`，发布走 version bump + update
- SessionStart hook 跑在每个会话里：必须 <100ms、任何异常静默 exit 0（`exec 2>/dev/null` + 一路 `|| exit 0`）
- stat 的 mtime 参数 macOS(`-f %m`) 与 Linux(`-c %Y`) 不同，hook 脚本要双分支
