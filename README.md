# claude-plugins

橙研所的 Claude Code plugin marketplace。

```
/plugin marketplace add libaoming/claude-plugins
/plugin install harness-kit@libaoming
```

## Plugins

| Plugin | 说明 |
|---|---|
| [harness-kit](plugins/harness-kit/) | 长程 agent 项目工程方法论：harness-init 项目脚手架（4 层防御体系）+ agent-memory-kit 运行时记忆层 + autoevolve prompt 自动进化环，外加骨架健康审计 agent 和会话进度注入 hook |

方法论本体（工具无关版）：[harness-kit](https://github.com/libaoming/harness-kit) · [agent-memory-kit](https://github.com/libaoming/agent-memory-kit)

## 本地开发

```bash
claude --plugin-dir ./plugins/harness-kit        # 加载开发版
claude plugin validate ./plugins/harness-kit --strict
```

本仓库自身用 harness 方法论管理（见 `features.json` / `STATUS.md`）——dogfooding。

## License

MIT
