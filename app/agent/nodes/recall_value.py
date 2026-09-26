"""召回字段取值节点：根据关键词从 Elasticsearch 检索字段的真实取值。"""

import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """输出节点进度，字段取值召回逻辑待实现。"""

    writer = runtime.stream_writer
    writer("召回字段取值")

    # 占位延时：便于观察流式输出中节点的执行顺序
    await asyncio.sleep(0.5)
