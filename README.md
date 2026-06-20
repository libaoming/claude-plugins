> 🌏 **English** | [中文](README.zh-CN.md)

# claude-plugins

橙研所's Claude Code plugin marketplace.

```
/plugin marketplace add libaoming/claude-plugins
/plugin install harness-kit@libaoming
```

## Plugins

| Plugin | Description |
|---|---|
| [harness-kit](plugins/harness-kit/) | Engineering methodology for long-running agent projects: the harness-init project scaffold (a 4-layer defense system) + the agent-memory-kit runtime memory layer + the autoevolve self-evolving prompt loop, plus a scaffold health-audit agent and a session progress-injection hook |

The methodology itself (tool-agnostic editions): [harness-kit](https://github.com/libaoming/harness-kit) · [agent-memory-kit](https://github.com/libaoming/agent-memory-kit)

## Local development

```bash
claude --plugin-dir ./plugins/harness-kit        # load the dev build
claude plugin validate ./plugins/harness-kit --strict
```

This repository is itself managed with the harness methodology (see `features.json` / `STATUS.md`) — dogfooding.

## License

MIT
