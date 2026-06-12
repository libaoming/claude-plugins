# Harness Kit (Claude Code Plugin)

把「长程 agent 项目工程方法论」打包成可安装的 Claude Code plugin。三个 skill + 一个只读审计 agent + 一个进度注入 hook，覆盖从项目初始化到 prompt 自动进化的完整工程链路。

方法论本体（工具无关版）见 [libaoming/harness-kit](https://github.com/libaoming/harness-kit)；运行时记忆层见 [libaoming/agent-memory-kit](https://github.com/libaoming/agent-memory-kit)。

## 组件

| 组件 | 调用 | 作用 |
|---|---|---|
| skill `harness-init` | `/harness-kit:harness-init` | 项目初始化唯一入口：4 层防御体系 scaffold（CLAUDE.md + STATUS + features.json + 切片三件套 + fixture + 只读运维子 agent），空目录新建与已有仓库纳管都适用 |
| skill `agent-memory-kit` | `/harness-kit:agent-memory-kit` | 给你构建的产品 agent 挂运行时记忆层：记忆四角色（Doer→Reflector→Store→检索注入）模板 |
| skill `autoevolve` | `/harness-kit:autoevolve` | 给任意 prompt/skill 挂自动进化环：6 文件骨架（program/judge/eval fixtures/记账） |
| agent `harness-auditor` | 自动或点名调用 | 只读骨架健康审计：features.json 标 passing 的有没有 verify 证据、STATUS 是否过期、三件套是否齐 |
| hook `SessionStart` | 自动 | 在 harness 项目里开会话时注入一行进度（x/y passing，当前切片，STATUS 新鲜度）；非 harness 项目零输出 |
| command `/harness-kit:status` | 手动 | 按需输出当前项目的 harness 进度表 |

## 三个 skill 的关系

```
harness-init（核心，所有项目）
 ├─ 默认产物：L1 持久化 + L2 方法论 + L3 hooks + L4 上下文隔离
 ├─ 可选挂载 → agent-memory-kit（你 build 的 agent 需要运行时记忆时）
 └─ 可选挂载 → autoevolve（要对 prompt 做闭环优化时）
```

注意区分两种记忆：L1 的 Auto Memory 是**开发时记忆**（Claude Code 跨会话接力）；agent-memory-kit 是**运行时记忆**（你构建的产品 agent 记住经验）。

## 安装

```
/plugin marketplace add libaoming/claude-plugins
/plugin install harness-kit@libaoming
```

本地开发调试：

```bash
claude --plugin-dir ./plugins/harness-kit
claude plugin validate ./plugins/harness-kit --strict
```

## License

MIT
