import json

from langchain_core.embeddings import Embeddings

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class QueryService:
    def __init__(
        self,
        meta_mysql_repository: MetaMySQLRepository,
        embedding_client: Embeddings,
        dw_mysql_repository: DWMySQLRepository,
        column_qdrant_repository: ColumnQdrantRepository,
        metric_qdrant_repository: MetricQdrantRepository,
        value_es_repository: ValueESRepository,
    ):
        # MySQL 仓储分别负责元数据补全和真实数仓环境信息读取
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository

        # 召回链路依赖的向量检索、Embedding 和全文检索能力由依赖层注入
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.value_es_repository = value_es_repository

    async def query(self, query: str):
        # State 只放会被图节点读写和合并的业务数据，外部工具对象不塞进 State
        # 节点会写入的字段在入口处一并置空值，后续由各节点逐步覆盖
        state = DataAgentState(
            query=query,
            keywords=[],
            retrieved_column_infos=[],
            retrieved_metric_infos=[],
            retrieved_value_infos=[],
            table_infos=[],
            metric_infos=[],
            date_info=DateInfoState(date="", weekday="", quarter=""),
            db_info=DBInfoState(dialect="", version=""),
            sql="",
            error=None,
        )

        # Context 保存本次图执行需要复用的外部依赖，节点通过 runtime.context 读取
        context = DataAgentContext(
            column_qdrant_repository=self.column_qdrant_repository,
            embedding_client=self.embedding_client,
            metric_qdrant_repository=self.metric_qdrant_repository,
            value_es_repository=self.value_es_repository,
            meta_mysql_repository=self.meta_mysql_repository,
            dw_mysql_repository=self.dw_mysql_repository,
        )

        try:
            # stream_mode="custom" 对应节点内部 writer(...) 写出的进度消息
            async for chunk in graph.astream(
                input=state,
                context=context,
                stream_mode="custom",
            ):
                # SSE 要求每条消息以 data: 开头，并以两个换行符结束
                # ensure_ascii=False 保留中文进度文案，default=str 兜底处理日期等非 JSON 类型
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        # ! 流式边界：响应头已经发出，无法再改状态码，所以任何异常都必须转成 error 事件
        except Exception as e:  # noqa: BLE001
            # 先把完整堆栈记进日志，再把失败作为一条 SSE 事件发给前端
            logger.exception("问数链路执行失败")
            error = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error, ensure_ascii=False, default=str)}\n\n"
