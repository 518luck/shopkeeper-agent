"""校验 SQL 节点：交给数仓解释执行，检查语法、表名和字段名。"""

import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """输出节点进度并写入校验结果，SQL 校验逻辑待实现。"""

    writer = runtime.stream_writer
    writer("校验SQL")

    # 占位延时：便于观察流式输出中节点的执行顺序
    await asyncio.sleep(0.5)

    # 骨架阶段固定返回无错误，让条件边走到 run_sql 分支
    return {"error": None}
