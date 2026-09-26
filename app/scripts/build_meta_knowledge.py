"""元数据知识库构建入口：初始化客户端、组装仓储与服务，启动一次完整构建。

只做装配与调度，构建逻辑全部在 MetaKnowledgeService。
"""

# 标准库：命令行参数解析、异步运行时、路径类型
import argparse
import asyncio
from pathlib import Path

# clients：各外部服务的客户端管理器，导入的已是模块级实例，可直接调用
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import (
    dw_mysql_client_manager,
    meta_mysql_client_manager,
)
from app.clients.qdrant_client_manager import qdrant_client_manager

# repositories：各存储的仓储类，需实例化后使用
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

# services：业务编排类，需实例化后使用
from app.services.meta_knowledge_service import MetaKnowledgeService


async def build(config_path: Path):
    """初始化所需客户端、组装仓储与 service，然后调用 service 完成构建。"""
    # 整条构建链路会用到 5 个基础服务：
    # 两套 MySQL（元数据库写、数仓读）、Qdrant 与 Embedding（字段/指标向量）、ES（字段取值全文索引）
    meta_mysql_client_manager.init()
    dw_mysql_client_manager.init()
    qdrant_client_manager.init()
    embedding_client_manager.init()
    es_client_manager.init()

    # 只有两套 MySQL 需要显式持有 Session，其余客户端由 repository 内部按需使用
    # 出块时自动关闭两个 session，块内即本次构建的完整生命周期
    async with (
        meta_mysql_client_manager.session_factory() as meta_session,
        dw_mysql_client_manager.session_factory() as dw_session,
    ):
        # meta 负责写元数据库，dw 负责读真实数仓的结构与字段取值
        meta_mysql_repository = MetaMySQLRepository(meta_session)
        dw_mysql_repository = DWMySQLRepository(dw_session)
        # 字段与指标分别写入不同的 Qdrant collection，后续可以独立召回
        column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)
        metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)
        value_es_repository = ValueESRepository(es_client_manager.client)
        # 向量化动作放在 service 层，这里只把客户端注入进去
        embedding_client = embedding_client_manager.client

        # 创建 service 对象，并把 repository 与客户端注入进去
        meta_knowledge_service = MetaKnowledgeService(
            meta_mysql_repository=meta_mysql_repository,
            dw_mysql_repository=dw_mysql_repository,
            column_qdrant_repository=column_qdrant_repository,
            embedding_client=embedding_client,
            value_es_repository=value_es_repository,
            metric_qdrant_repository=metric_qdrant_repository,
        )

        # 真正进入服务层的构建逻辑
        await meta_knowledge_service.build(config_path)

    # 结束后关闭所有客户端连接
    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
    await qdrant_client_manager.close()
    await es_client_manager.close()


if __name__ == "__main__":
    # 仅直接运行本模块时进入；被 import 时不执行
    # 解析命令行参数，由外部决定本次构建使用哪份配置文件
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf", required=True)
    args = parser.parse_args()

    # 字符串路径转 Path 后传给 build；asyncio.run 启动事件循环执行异步入口
    asyncio.run(build(Path(args.conf)))
