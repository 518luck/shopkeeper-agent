# app/entities

适用：系统内部流转的数据载体（业务实体）。

## 必须

- 一实体一模块。

### 定义

- 用 `@dataclass`；只声明字段，不写方法。
- 字段名与落库/索引侧一致（ORM 模型属性名、ES 文档键）：`asdict` 直传与 payload 往返都依赖它。
- 容器标参数（`list[str]` / `list[Any]`），不用裸 `list`。

### 取值

- 字段值必须可 JSON 序列化：要写进 JSON 列与 Qdrant payload。
- `Decimal` / `datetime` 在上游转成 `float` / ISO 字符串后再放进实体。

### 转换

- 实体 ↔ ORM 模型的转换只在 mapper 中做。

## 禁止

- 引用存储与外部服务模块（`sqlalchemy` / `repositories` / `clients` / `services`）。
- 实体里写行为（查询、转换、调外部服务）。
- 新增实体后遗漏接线：落库或索引所需的模型与 mapper。
