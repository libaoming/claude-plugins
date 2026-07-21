# STATUS — {{PROJECT}}

> 每次 session 第一个读的文件。收尾必更新本文件。

## 一句话状态
{{DATE}} 项目脚手架完成（4 层骨架就位），**文档先行进行中**：PRD/SPEC/architecture 待填，未开始写代码。

## 下次入口
1. 读本文件 → 读 `{{MILESTONE}}/PROGRESS.md`
2. 跑 `bash {{MILESTONE}}/init.sh` 确认环境
3. 当前应做：和用户一起填 `PRD.md`（L2 文档先行，没写完不许写代码）

## 关键技术事实
- （待补：技术栈 / 外部依赖 / 账号资源）

## 文档地图
- 需求：`PRD.md`　方案：`SPEC.md`　架构：`architecture.md`　切片：`features.json`
- 里程碑三件套：`{{MILESTONE}}/`　fixture：`fixtures/`
- 脏活隔离子 agent：`.claude/agents/{{PROJECT}}-ops.md`

## 踩坑清单
- （随项目积累）

## 能力假设登记（模型大版本升级时体检）

> CLAUDE.md 里的**行为补丁类**纪律，每条都在对抗「当前模型的弱点」，会随模型变强过期（官方先例：显式 context reset 在自动 compaction 成熟后被移除）。每次大版本模型升级（如 Opus 4.8 → Fable 5）后逐条自问：**「这条还在对抗一个存在的问题吗？」**——不在了就删机制并在下表记录。**治理层不登记**（verify 硬闸门 / fixture 先行 / exit_criteria / 不可逆动作人工确认）：它们对抗的是任何执行者都有的问题，不过期。

| 补丁 | 对抗的模型弱点 | 上次体检 |
|---|---|---|
| feature 清单用 JSON 不用 Markdown | 乱改/覆盖 Markdown 清单 | {{DATE}} |
| 线性切片切细 + 一次一个 feature | one-shot 半途 context 耗尽、过早宣告完成 | {{DATE}} |
| 固定入会顺序（STATUS → 三件套 → init.sh） | 冷启动失忆 | {{DATE}} |
| L3 stop-progress-append 增量流水 | 会话中断丢进度 | {{DATE}} |
| L3 stop-verify-claims 防造假收口闸 + 反安慰性重跑 | 幻觉式执行声明 | {{DATE}} |
| L4 大文档检索必须派子 agent | context 稀缺、attention 稀释（仅容量动机会过期；「新鲜大脑防自审偏差」不过期） | {{DATE}} |
