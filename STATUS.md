# STATUS — claude-plugins

**一句话状态**：M1 全部 passing（S1-S6）——harness-kit v0.1.1 已发布到 github.com/libaoming/claude-plugins，从 marketplace 安装的 cache 副本 verify 通过，用户级 harness-init skill 已归档（plugin 版接管，调用名变为 `/harness-kit:harness-init`）。

**下次入口**：
1. S7（可选）：把各切片「学到的机制」整理成橙研所拆解文章（素材：features.json 的 verify_notes + 本文件踩坑清单）
2. 后续迭代：改 plugin 源码 → bump version → push → `claude plugin update harness-kit@libaoming`（本地试验用 `--plugin-dir`）

**踩坑清单**：
- plugin 内不能引用 plugin 外路径（marketplace 安装只复制 plugin 目录）——templates 必须随 skill 走；同 plugin 内跨 skill 相对引用（`../`）安全
- marketplace 安装是复制：装完改源码不生效，开发用 `--plugin-dir`，发布走 version bump + update
- SessionStart hook 跑在每个会话里：必须 <100ms、任何异常静默 exit 0（`exec 2>/dev/null` + 一路 `|| exit 0`）
- stat 的 mtime 参数 macOS(`-f %m`) 与 Linux(`-c %Y`) 不同，hook 脚本要双分支
