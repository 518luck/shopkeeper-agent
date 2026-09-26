"""召回指标信息节点：根据关键词从 Qdrant 检索候选业务指标。"""

import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """输出节点进度，指标召回逻辑待实现。"""

    writer = runtime.stream_writer
    writer("召回指标信息")

    # 占位延时：便于观察流式输出中节点的执行顺序
    await asyncio.sleep(0.5)
