"""生成 SQL 节点：基于整理后的上下文调用大模型生成 SQL。"""

import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState


async def generate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """输出节点进度，SQL 生成逻辑待实现。"""

    writer = runtime.stream_writer
    writer("生成SQL")

    # 占位延时：便于观察流式输出中节点的执行顺序
    await asyncio.sleep(0.5)
