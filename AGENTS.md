# AGENTS.md

教学文档（本地原文，优先查这里）：
`/Users/duoyun/work/study/study-agent/ai-agents-from-zero/`
→ 本项目章节在 `实战项目-电商问数/`（命名 `章节号-标题.md`）；大纲 `_sidebar.md`；在线版 https://didilili.github.io/ai-agents-from-zero/#/

用户是前端工程师，讲 Python 用 JS/TS 类比；改完代码用 `uv run python` / `uvx pyright` 验证。

新增或修改 AI 约束（本文件及同类规则文件）时遵循「空白优于长篇大论」：能删就删，不写没有信息量的内容。

类型断言优先 `assert isinstance`（运行时校验 + 类型收窄）；`cast` 只用于类型信息在库边界丢失处，单表达式、不 cast 到 `Any`、写明理由；pyright 开 `reportUnnecessaryCast = "warning"`。
