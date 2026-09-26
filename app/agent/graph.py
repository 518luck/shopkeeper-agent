"""问数智能体工作流图：注册节点与边，编译成可运行图。

骨架阶段各节点只输出进度，用于验证图能编译、节点能被调度、进度能流式输出。
"""

import asyncio

from langgraph.constants import END, START
from langgraph.graph import StateGraph

from app.agent.context import DataAgentContext
from app.agent.nodes.add_extra_context import add_extra_context
from app.agent.nodes.correct_sql import correct_sql
from app.agent.nodes.extract_keywords import extract_keywords
from app.agent.nodes.filter_metric import filter_metric
from app.agent.nodes.filter_table import filter_table
from app.agent.nodes.generate_sql import generate_sql
from app.agent.nodes.merge_retrieved_info import merge_retrieved_info
from app.agent.nodes.recall_column import recall_column
from app.agent.nodes.recall_metric import recall_metric
from app.agent.nodes.recall_value import recall_value
from app.agent.nodes.run_sql import run_sql
from app.agent.nodes.validate_sql import validate_sql
from app.agent.state import DataAgentState

# 图构建器：声明共享状态与运行时上下文的 Schema，节点签名和调用方据此做类型检查
graph_builder = StateGraph(
    state_schema=DataAgentState,
    context_schema=DataAgentContext,
)

# 注册节点：名称与函数名保持一致，便于连边、看日志和看流程图
graph_builder.add_node("extract_keywords", extract_keywords)  # 抽取关键词
graph_builder.add_node("recall_column", recall_column)  # 召回字段信息
graph_builder.add_node("recall_value", recall_value)  # 召回字段取值
graph_builder.add_node("recall_metric", recall_metric)  # 召回指标信息
graph_builder.add_node("merge_retrieved_info", merge_retrieved_info)  # 合并召回信息
graph_builder.add_node("filter_metric", filter_metric)  # 过滤指标信息
graph_builder.add_node("filter_table", filter_table)  # 过滤表信息
graph_builder.add_node("add_extra_context", add_extra_context)  # 添加额外上下文
graph_builder.add_node("generate_sql", generate_sql)  # 生成 SQL
graph_builder.add_node("validate_sql", validate_sql)  # 校验 SQL
graph_builder.add_node("correct_sql", correct_sql)  # 校正 SQL
graph_builder.add_node("run_sql", run_sql)  # 执行 SQL

graph_builder.add_edge(START, "extract_keywords")

# 关键词就绪后三路召回并行：字段找列、指标找口径、取值找过滤条件的真实值
graph_builder.add_edge("extract_keywords", "recall_column")
graph_builder.add_edge("extract_keywords", "recall_value")
graph_builder.add_edge("extract_keywords", "recall_metric")

# 三路召回都完成后才汇入合并节点
graph_builder.add_edge("recall_column", "merge_retrieved_info")
graph_builder.add_edge("recall_value", "merge_retrieved_info")
graph_builder.add_edge("recall_metric", "merge_retrieved_info")

# 表过滤与指标过滤并行
graph_builder.add_edge("merge_retrieved_info", "filter_table")
graph_builder.add_edge("merge_retrieved_info", "filter_metric")

# 两个过滤都完成后才补齐上下文
graph_builder.add_edge("filter_table", "add_extra_context")
graph_builder.add_edge("filter_metric", "add_extra_context")

graph_builder.add_edge("add_extra_context", "generate_sql")
graph_builder.add_edge("generate_sql", "validate_sql")


def route_after_validate(state: DataAgentState) -> str:
    """校验无错误则执行 SQL，有错误则先校正。"""

    return "run_sql" if state.get("error") is None else "correct_sql"


# 条件边：validate_sql 之后不是固定流转，按校验结果二选一
graph_builder.add_conditional_edges(
    source="validate_sql",  # 分支起点
    path=route_after_validate,  # 分支函数：读 state 里的 error 决定下一跳
    path_map={
        "run_sql": "run_sql",
        "correct_sql": "correct_sql",
    },  # 返回值 → 实际要去的节点名
)
graph_builder.add_edge("correct_sql", "run_sql")  # 校正之后仍然要执行
graph_builder.add_edge("run_sql", END)  # 执行完，图结束

graph = graph_builder.compile()


async def demo():
    """跑一次图并打印进度，验证编译、调度顺序和流式输出是否正常。"""

    state = DataAgentState(query="统计华北地区的销售总额")
    context = DataAgentContext()

    async for chunk in graph.astream(
        input=state, context=context, stream_mode="custom"
    ):
        print(chunk)


if __name__ == "__main__":
    asyncio.run(demo())
