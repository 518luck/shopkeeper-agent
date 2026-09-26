"""
`column_metric` ORM 模型

定义元数据库中 column_metric 表对应的 ORM 模型
负责保存字段和指标之间的关联关系，方便后续从字段追踪相关指标，或者从指标回查依赖字段
"""

# 列类型：String → varchar
from sqlalchemy import String

# Mapped 标注 Python 侧类型，mapped_column 定义数据库侧的真实列
from sqlalchemy.orm import Mapped, mapped_column

# 项目统一的 ORM 基类，继承它才会被映射成表
from app.models.base import Base


class ColumnMetricMySQL(Base):
    """字段与指标关联关系表对应的 ORM 模型"""

    __tablename__ = "column_metric"

    # 这里采用联合主键
    # 表示同一对 字段 指标 关系只允许出现一次
    column_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="列编号"
    )
    metric_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="指标编号"
    )
