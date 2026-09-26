"""问数智能体在图节点之间共享的状态结构。"""

from typing import NotRequired, TypedDict


class DataAgentState(TypedDict):
    """一次问数链路中的核心状态。"""

    query: str  # 用户输入的查询
    # 校验通过前这个键不存在，所以声明为可选：读取时用 get 而不是下标
    error: NotRequired[str | None]  # 校验SQL时出现的错误信息
