# fixtures 索引

verify 引用的 fixture 都在此。**fixture 先于代码**：feature 的 verify 指向的 fixture 不存在 → 先造，不许 mock、不许"等真数据"。优先设计"一段 fixture 养活多条 feature"的复用结构。

| fixture | 状态 | 用途 / 喂哪些 feature |
|---|---|---|
| `example/` | 待造 | F01_example |
