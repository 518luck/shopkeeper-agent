"""
`metric_info` ORM 模型

定义元数据库中 metric_info 表对应的 ORM 模型
负责保存指标名称 指标说明 指标别名，以及指标和底层字段之间的关联关系
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base


class MetricInfoMySQL(Base):
    """指标元数据表对应的 ORM 模型"""

    __tablename__ = "metric_info"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, comment="指标编码")
    # 元数据写入时这些字段必有值，因此声明为非 Optional：
    # 这样 Mapper 的 to_entity（ORM -> 实体）才不需要额外判空
    name: Mapped[str] = mapped_column(String(128), comment="指标名称")
    description: Mapped[str] = mapped_column(Text, comment="指标描述")
    # 指标通常会关联一个或多个底层字段
    # 这里直接以 JSON 数组保存字段标识列表
    relevant_columns: Mapped[list[str]] = mapped_column(JSON, comment="关联字段")
    alias: Mapped[list[str]] = mapped_column(JSON, comment="指标别名")
