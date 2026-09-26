from dataclasses import dataclass
from enum import Enum


class TableRole(str, Enum):
    """meta_config.yaml 中表 role 的允许取值"""

    dim = "dim"
    fact = "fact"


class ColumnRole(str, Enum):
    """meta_config.yaml 中字段 role 的允许取值"""

    primary_key = "primary_key"
    foreign_key = "foreign_key"
    dimension = "dimension"
    measure = "measure"


@dataclass
class ColumnConfig:
    name: str
    role: ColumnRole
    description: str
    alias: list[str]
    sync: bool


@dataclass
class TableConfig:
    name: str
    role: TableRole
    description: str
    columns: list[ColumnConfig]


@dataclass
class MetricConfig:
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


@dataclass
class MetaConfig:
    # 允许只同步表，或只同步指标，所以两个字段都做成 Optional
    tables: list[TableConfig] | None = None
    metrics: list[MetricConfig] | None = None
