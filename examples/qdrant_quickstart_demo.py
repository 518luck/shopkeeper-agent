# Qdrant 快速入门：建集合 → 写向量 → 查相似度
# 运行前提：Qdrant 容器已启动（在 docker/ 目录执行 docker compose up -d）
# 运行方式（在项目根目录）：uv run python -m examples.qdrant_quickstart_demo

# asyncio 是标准库里的异步运行时（事件循环 + await 机制），≈ Node 内置的 event loop，不用安装
import asyncio

# 官方客户端库一次导入两样东西：
#   AsyncQdrantClient —— 异步客户端类，负责发请求
#   models            —— 数据结构的命名空间（PointStruct / VectorParams / Distance…），≈ `import * as models`
from qdrant_client import AsyncQdrantClient, models

# 服务地址：docker-compose 把容器的 6333 映射到了本机 6333
QDRANT_URL = "http://localhost:6333"
# 集合名 ≈ MySQL 里的"表名"，同类向量放在同一个集合里
COLLECTION_NAME = "quickstart_demo"
# 向量维度：演示用 4 维是为了肉眼能看清数字；
# 真实项目里必须和 embedding 模型的输出维度一致（bge-large-zh-v1.5 是 1024）
VECTOR_SIZE = 4


async def recreate_collection(client):
    """为了让示例可重复运行，先删除旧集合，再重新创建"""
    # await ≈ JS 的 await：等异步操作完成再往下走。
    # 不 await 拿到的是"待执行的协程对象"，而不是 True/False。
    # 先删再建 ≈ DROP TABLE IF EXISTS + CREATE TABLE，保证从干净状态开始
    if await client.collection_exists(COLLECTION_NAME):
        await client.delete_collection(COLLECTION_NAME)

    # Create a collection：创建一个新的集合（≈ CREATE TABLE）
    # 命名参数 name=value ≈ JS 的 options 对象，只是不用写花括号
    await client.create_collection(
        collection_name=COLLECTION_NAME,
        # 声明这个集合里的向量长什么样：维度 + 用什么方式比"像不像"
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,  # 必须等于写入向量的长度，否则 upsert 直接报错
            distance=models.Distance.COSINE,  # 余弦距离，决定后面 score 的算法
        ),
    )
    # f-string ≈ 模板字符串；print ≈ console.log
    print(f"1. 已创建集合：{COLLECTION_NAME}")


async def add_vectors(client):
    """
    写入几个示例向量

    这里同时带上 payload，方便读者理解：
    在 Qdrant 里，一个 point 不只有 vector，还可以附带业务字段
    """
    # upsert = update + insert：id 已存在就整体覆盖，不存在就新增
    # （SQL 里对应 INSERT ... ON DUPLICATE KEY UPDATE）
    await client.upsert(
        collection_name=COLLECTION_NAME,
        # 一次批量写多个点，比循环单条写省掉大量网络往返
        points=[
            # 一个 point = id + vector + payload 三件套：
            #   id      点的主键。演示里用 1/2/3；真实项目用 uuid，因为一个字段会被拆成多个点
            #   vector  长度必须等于建集合时声明的 size
            #   payload 附带的业务数据，dict ≈ JS 对象字面量；检索命中后会原样返回
            models.PointStruct(
                id=1,
                vector=[0.05, 0.61, 0.76, 0.74],
                payload={"name": "订单分析", "type": "report"},
            ),
            models.PointStruct(
                id=2,
                vector=[0.19, 0.81, 0.75, 0.11],
                payload={"name": "销量趋势", "type": "metric"},
            ),
            models.PointStruct(
                id=3,
                vector=[0.36, 0.55, 0.47, 0.94],
                payload={"name": "区域销售额", "type": "dimension"},
            ),
        ],
    )
    print("2. 已写入 3 个向量点。")


async def run_query(client):
    """
    执行一次向量查询

    查询向量会和集合里的点做相似度计算，
    最终返回最相近的几个 point
    """
    # 待检索的向量。这里手写一个是为了演示：
    # 真实项目里它由 Embedding 服务把用户问题转出来，再拿来检索
    query_vector = [0.2, 0.1, 0.9, 0.7]
    # query_points 就是"检索"：和集合里每个点算相似度，返回最像的前 limit 个
    result = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=3,  # top-k：只要最像的 3 条
        with_payload=True,  # 结果里带上 payload；设 False 只返回 id/score，省流量但还得自己回查
    )

    print(f"3. 查询向量：{query_vector}")
    print("4. 查询结果：")
    # enumerate ≈ JS 数组的 .entries()：同时拿到下标和元素；start=1 让序号从 1 开始
    for i, point in enumerate(result.points, start=1):
        # score 是相似度得分，越接近 1 越像；:.4f 保留 4 位小数（≈ toFixed(4)）
        # point 是对象，用 . 取属性，和 JS 一样
        print(
            f"   {i}) id={point.id}, score={point.score:.4f}, payload={point.payload}"
        )


async def main():
    # 直接初始化客户端，方便单独学习 quickstart 的基本用法
    # 构造时只是记下连接配置，没有 await —— 真正的网络请求发生在后面每个方法被 await 时
    client = AsyncQdrantClient(url=QDRANT_URL)

    # try/finally ≈ JS 的同名语法：无论中间是否抛异常，finally 一定执行
    try:
        await recreate_collection(client)
        await add_vectors(client)
        await run_query(client)
    finally:
        # 关闭连接、释放资源；异步客户端的 close() 也要 await，漏掉会留下未关闭的连接
        await client.close()


# ≈ Node 里的 if (require.main === module)：只有直接运行本文件时才执行，被 import 时不执行
if __name__ == "__main__":
    # 启动事件循环、跑完 main() 后退出（Python 不允许在模块顶层直接写 await）
    asyncio.run(main())
