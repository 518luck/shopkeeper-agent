"""额外上下文节点：补齐 SQL 生成所需的当前日期与数据库方言信息。"""

import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState


async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """输出节点进度，日期与数据库信息补全逻辑待实现。"""

    writer = runtime.stream_writer
    writer("添加额外上下文")

    # 占位延时：便于观察流式输出中节点的执行顺序
    await asyncio.sleep(0.5)
