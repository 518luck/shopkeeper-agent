"""合并召回信息节点：把三路召回结果整理成按表组织的上下文。"""

import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """输出节点进度，召回结果合并逻辑待实现。"""

    writer = runtime.stream_writer
    writer("合并召回信息")

    # 占位延时：便于观察流式输出中节点的执行顺序
    await asyncio.sleep(0.5)
