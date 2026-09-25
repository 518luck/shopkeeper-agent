# AGENTS.md

## 生成本文件

- 目标：极简操作契约，非项目文档。
- 只输出 Markdown 文件内容；不解释、不总结、不寒暄。
- 能推断的不写：README、package.json、pyproject.toml、Makefile、lint/format/test 配置、目录结构。改写成「遵循 <路径/工具默认>」。
- 不写：项目介绍、架构、目录树、背景、原因、示例、通用最佳实践、重复配置。
- 不写软词：请、建议、可以、注意、应该、尽量。
- 用祈使句/清单/键值对。
- 无内容则省略该节，不硬凑。
- 不确定写 TODO 或留空，禁止编造。

## 注释约束：

- 函数/类/模块首行一句话概括用途。
- 默认普通注释，不加 `>` / `!`。
- 仅必要时：`> ` 标重点逻辑；`! ` 标坑/危险/约束/安全。

## 教学文档

- 本地原文优先：`/Users/duoyun/work/study/study-agent/ai-agents-from-zero/`
- 本项目章节：`实战项目-电商问数/`；命名 `章节号-标题.md`；大纲 `_sidebar.md`

## 交流

- 讲 Python 用 JS/TS 类比。

## 交付

- 改完代码跑：`uv run python -m <模块>`、`uvx pyright app/`
- 检查与格式化配置遵循 `pyproject.toml`；TODO：补 `reportUnnecessaryCast = "warning"`

## 类型

- 断言优先 `assert isinstance`：运行时校验 + 类型收窄。
- `cast` 仅用于库边界信息丢失处；单表达式；不 cast 到 `Any`；写明理由。

## TypedDict

- 形式：class 语法；非必要不用函数式 `TypedDict("X", {...})`。
- 数据形状（LLM 结构化输出、JSON、Agent 状态）：`total=True`；可选字段 `NotRequired[T]`。
- 函数参数（`**kwargs: Unpack[T]`）：`total=False`；必传参数 `Required[T]`。
- 样板：`app/clients/embedding_client_manager.py` 的 `EmbeddingInitKwargs`。
