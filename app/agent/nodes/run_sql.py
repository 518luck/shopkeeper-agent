"""执行 SQL 节点：在数仓上真正执行 SQL 并返回查询结果。"""

import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState


async def run_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """输出节点进度，SQL 执行逻辑待实现。"""

    writer = runtime.stream_writer
    writer("执行SQL")

    # 占位延时：便于观察流式输出中节点的执行顺序
    await asyncio.sleep(0.5)
