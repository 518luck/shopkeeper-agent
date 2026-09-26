import uuid
from dataclasses import asdict
from pathlib import Path

from langchain_core.embeddings import Embeddings
from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    # 接收入口注入的仓储与客户端并持有，不做业务流程
    def __init__(
        self,
        meta_mysql_repository: MetaMySQLRepository,
        dw_mysql_repository: DWMySQLRepository,
        column_qdrant_repository: ColumnQdrantRepository,
        embedding_client: Embeddings,
        value_es_repository: ValueESRepository,
        metric_qdrant_repository: MetricQdrantRepository,
    ):
        # meta repository 负责结构化元数据的落库
        self.meta_mysql_repository: MetaMySQLRepository = meta_mysql_repository
        # dw repository 负责到教学数仓中读取真实表结构和示例值
        self.dw_mysql_repository: DWMySQLRepository = dw_mysql_repository
        # 字段向量集合的创建与批量写入
        self.column_qdrant_repository: ColumnQdrantRepository = column_qdrant_repository
        # 向量化动作放在 Service 层，仓储只负责落库
        self.embedding_client: Embeddings = embedding_client
        # 字段真实值的全文索引写入
        self.value_es_repository: ValueESRepository = value_es_repository
        # 指标向量单独一个 collection，便于按对象类型独立召回
        self.metric_qdrant_repository: MetricQdrantRepository = metric_qdrant_repository

    # 构建总流程：读配置 → 表链路 → 指标链路
    async def build(self, config_path: Path):
        # 1. 读取配置文件并转换成结构化配置对象
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        # to_object 的返回类型是 Union[...]，用 assert isinstance 做运行时校验并让类型检查器收窄
        result = OmegaConf.to_object(OmegaConf.merge(schema, context))
        assert isinstance(result, MetaConfig), f"配置加载失败: {type(result)}"
        meta_config: MetaConfig = result
        logger.info("加载配置文件")

        # 2. 表链路：Meta MySQL -> 字段向量索引 -> 字段值全文索引
        if meta_config.tables:
            column_infos = await self._save_tables_to_meta_db(meta_config)
            logger.info(f"表与字段元数据已写入 Meta MySQL，字段数：{len(column_infos)}")
            await self._save_column_info_to_qdrant(column_infos)
            logger.info("字段向量索引已写入 Qdrant")
            await self._save_value_info_to_es(meta_config, column_infos)
            logger.info("字段取值全文索引已写入 Elasticsearch")

        # 3. 指标链路：Meta MySQL -> 指标向量索引
        if meta_config.metrics:
            metric_infos = await self._save_metrics_to_meta_db(meta_config)
            logger.info(f"指标与字段关联已写入 Meta MySQL，指标数：{len(metric_infos)}")
            await self._save_metrics_to_qdrant(metric_infos)
            logger.info("指标向量索引已写入 Qdrant")

        logger.info("元数据知识库构建完成")

    # 表链路①：配置 + 数仓 → 表/字段实体，写入 Meta MySQL 并返回字段实体
    async def _save_tables_to_meta_db(
        self, meta_config: MetaConfig
    ) -> list[ColumnInfo]:
        """把配置中的表和字段加工成业务实体并写入 Meta MySQL，返回字段实体供后续建索引。"""
        table_infos: list[TableInfo] = []
        column_infos: list[ColumnInfo] = []

        # tables 在配置里是可选的；调用方已判空，这里断言收窄掉 None
        tables = meta_config.tables
        assert tables is not None, "tables 为空时不应进入表链路"

        for table in tables:
            # 表级实体：4 个字段全部来自配置，不需要查 DW
            table_info = TableInfo(
                id=table.name,
                name=table.name,
                # 枚举成员取 .value，否则格式化时会得到 "TableRole.dim"
                role=table.role.value,
                description=table.description,
            )
            table_infos.append(table_info)

            # 字段类型按【表】查一次：一条 show columns 就能拿到全表类型
            column_types: dict[
                str, str
            ] = await self.dw_mysql_repository.get_column_types(table.name)

            for column in table.columns:
                # 示例值按【字段】查（一列一查），只取 10 条；全量取值留到 ES 那一步
                column_values: list = await self.dw_mysql_repository.get_column_values(
                    table.name, column.name, 10
                )
                # 6 个字段来自配置（业务语义），type / examples 来自 DW（真实结构与样本）
                column_info = ColumnInfo(
                    # 唯一标识用「表名.字段名」，避免跨表同名字段（如 customer_id）冲突
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_types[column.name],
                    role=column.role.value,
                    examples=column_values,
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name,
                )
                column_infos.append(column_info)

        # 表信息与字段信息属于同一批业务操作：放在一个事务里，一起成功或一起回滚
        async with self.meta_mysql_repository.session.begin():
            self.meta_mysql_repository.save_table_infos(table_infos)
            self.meta_mysql_repository.save_column_infos(column_infos)

        return column_infos

    # 表链路②：字段实体拆成语义入口 → 向量化 → 写 Qdrant
    async def _save_column_info_to_qdrant(self, column_infos: list[ColumnInfo]):
        """把字段实体拆成多个语义入口，向量化后写入字段向量 collection。"""
        await self.column_qdrant_repository.ensure_collection()

        # 一个字段拆成多个 point，每个 point 的 payload 都是完整的字段信息
        points: list[dict] = []
        for column_info in column_infos:
            # 字段名、描述、每个别名各建一个 point，覆盖不同的说法
            for embedding_text in (
                column_info.name,
                column_info.description,
                *column_info.alias,
            ):
                points.append(
                    {
                        # 一个字段拆成多个 point，所以 point id 不能复用 column_info.id
                        "id": uuid.uuid4(),
                        "embedding_text": embedding_text,
                        "payload": asdict(column_info),
                    }
                )

        embeddings = await self._embed_texts([p["embedding_text"] for p in points])

        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.column_qdrant_repository.upsert(ids, embeddings, payloads)

    # 表链路③：按 sync 开关取字段真实取值 → 写 ES 全文索引
    async def _save_value_info_to_es(
        self, meta_config: MetaConfig, column_infos: list[ColumnInfo]
    ):
        """按配置里的 sync 开关，把字段真实取值写入 ES 全文索引。"""
        await self.value_es_repository.ensure_index()

        # 把配置整理成「字段 id -> 是否同步真实值」的快速查询表，避免嵌套遍历配置
        tables = meta_config.tables
        assert tables is not None, "tables 为空时不应进入取值同步链路"
        column2sync: dict[str, bool] = {}
        for table in tables:
            for column in table.columns:
                # 字段 id 要和 ColumnInfo.id 的拼法保持一致
                column2sync[f"{table.name}.{column.name}"] = column.sync

        value_infos: list[ValueInfo] = []
        for column_info in column_infos:
            if not column2sync[column_info.id]:
                continue
            # 这里要的是字段值域全集（不再只取 10 条示例），用足够大的 limit 近似拿全
            current_column_values = await self.dw_mysql_repository.get_column_values(
                column_info.table_id, column_info.name, 100000
            )
            value_infos.extend(
                ValueInfo(
                    # 字段 id + 字段值 组成一条值记录的唯一 id
                    id=f"{column_info.id}.{value}",
                    value=value,
                    # 记录这个值属于哪个字段，命中后便于反查字段上下文
                    column_id=column_info.id,
                )
                for value in current_column_values
            )

        await self.value_es_repository.index(value_infos)

    # 指标链路①：配置 → 指标实体 + 字段关联，写入 Meta MySQL 并返回指标实体
    async def _save_metrics_to_meta_db(
        self, meta_config: MetaConfig
    ) -> list[MetricInfo]:
        """把指标定义与「指标依赖哪些字段」的关系写入 Meta MySQL。"""
        metric_infos: list[MetricInfo] = []
        column_metrics: list[ColumnMetric] = []

        # metrics 在配置里是可选的；调用方已判空，这里断言收窄掉 None
        metrics = meta_config.metrics
        assert metrics is not None, "metrics 为空时不应进入指标链路"

        for metric in metrics:
            # 指标名本身就是配置里的唯一业务标识，直接作为 id
            metric_infos.append(
                MetricInfo(
                    id=metric.name,
                    name=metric.name,
                    description=metric.description,
                    relevant_columns=metric.relevant_columns,
                    alias=metric.alias,
                )
            )
            for column in metric.relevant_columns:
                # 单独表达「某个指标依赖某个字段」这层关系
                column_metrics.append(
                    ColumnMetric(column_id=column, metric_id=metric.name)
                )

        # 指标本身和字段关系属于同一批业务操作：放在一个事务里
        async with self.meta_mysql_repository.session.begin():
            self.meta_mysql_repository.save_metric_infos(metric_infos)
            self.meta_mysql_repository.save_column_metrics(column_metrics)

        return metric_infos

    # 指标链路②：指标实体拆成语义入口 → 向量化 → 写 Qdrant
    async def _save_metrics_to_qdrant(self, metric_infos: list[MetricInfo]):
        """把指标拆成多个语义入口，向量化后写入指标向量 collection。"""
        await self.metric_qdrant_repository.ensure_collection()

        points: list[dict] = []
        for metric_info in metric_infos:
            # 和字段一样：指标名、描述、每个别名各建一个 point
            for embedding_text in (
                metric_info.name,
                metric_info.description,
                *metric_info.alias,
            ):
                points.append(
                    {
                        "id": uuid.uuid4(),
                        "embedding_text": embedding_text,
                        "payload": asdict(metric_info),
                    }
                )

        embeddings = await self._embed_texts([p["embedding_text"] for p in points])

        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)

    # 公共工具：分批向量化，两处 Qdrant 写入共用
    async def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """分批调用 Embedding 服务；返回顺序与输入文本顺序严格一致。"""
        embeddings: list[list[float]] = []
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings.extend(await self.embedding_client.aembed_documents(batch))
        return embeddings
