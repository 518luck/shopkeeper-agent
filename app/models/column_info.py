"""
`column_info` ORM 模型

定义元数据库中 column_info 表对应的 ORM 模型
保存字段级元数据，包括字段类型 字段角色 示例值 说明 别名 以及所属表
"""

# Any：examples 里装的取值类型不定（可能是数字/字符串/日期）
from typing import Any

# 列类型：String → varchar，Text → text
from sqlalchemy import String, Text

# Mapped 标注 Python 侧类型，mapped_column 定义数据库侧的真实列
from sqlalchemy.orm import Mapped, mapped_column

# JSON 对应 MySQL 的 JSON 列，用来存列表（examples / alias）
from sqlalchemy.types import JSON

# 项目统一的 ORM 基类，继承它才会被映射成表
from app.models.base import Base


class ColumnInfoMySQL(Base):
    """字段元数据表对应的 ORM 模型"""

    __tablename__ = "column_info"

    # id 采用 表名.字段名 的组合形式
    # 这样在整个数仓范围内更容易保证唯一性
    # 长度与建表脚本（varchar(128)）保持一致
    id: Mapped[str] = mapped_column(String(128), primary_key=True, comment="列编号")
    # 元数据写入时这些字段必有值，因此声明为非 Optional：
    # 这样 Mapper 的 to_entity（ORM -> 实体）才不需要额外判空
    name: Mapped[str] = mapped_column(String(128), comment="列名称")
    type: Mapped[str] = mapped_column(String(64), comment="数据类型")
    role: Mapped[str] = mapped_column(
        String(32), comment="列类型(primary_key,foreign_key,measure,dimension)"
    )
    # examples 和 alias 都使用 JSON 存储
    # 方便保存列表结构而不是再拆独立子表
    examples: Mapped[list[Any]] = mapped_column(JSON, comment="数据示例")
    description: Mapped[str] = mapped_column(Text, comment="列描述")
    alias: Mapped[list[str]] = mapped_column(JSON, comment="列别名")
    table_id: Mapped[str] = mapped_column(String(64), comment="所属表编号")
