# ES 客户端封装：上半部分是管理器，下半部分是最小可运行演示
# 运行前提：ES 容器已启动（在 docker/ 目录执行 docker compose up -d）
# 运行方式（在项目根目录）：uv run python -m app.clients.es_client_manager

import asyncio

# 官方异步客户端，作用相当于前端的 @elastic/elasticsearch
from elasticsearch import AsyncElasticsearch

# 配置对象：host / port / index_name 都来自项目根目录的 conf/app_config.yaml
from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    def __init__(self, es_config: ESConfig):
        # 保存 ES 配置对象，后面初始化客户端时会从这里读取 host 和 port
        self.es_config = es_config
        # 先用私有属性声明出来，真正初始化放到 init() 中进行
        # （和 QdrantClientManager 完全同一套写法，便于统一生命周期管理）
        self._client: AsyncElasticsearch | None = None

    @property
    def client(self) -> AsyncElasticsearch:
        # 对外暴露的客户端一定是已初始化的：断言既能让类型检查器收窄掉 None，
        # 也能把“忘记调用 init()”从难懂的 AttributeError 变成明确的报错
        assert self._client is not None, "ES 客户端尚未初始化，请先调用 init()"
        return self._client

    def _get_url(self):
        # 根据配置文件拼出 ES 服务地址
        return f"http://{self.es_config.host}:{self.es_config.port}"

    def init(self):
        # 创建异步 ES 客户端
        # hosts 之所以是列表，是为了兼容 ES 常见的集群连接方式：
        # 列表里可以放多个节点，客户端会自动做负载均衡和故障转移（单机开发就一个）
        self._client = AsyncElasticsearch(hosts=[self._get_url()])

    async def close(self):
        # 在程序退出时统一关闭客户端连接；没初始化过就什么都不做，允许重复调用
        if self._client is not None:
            await self._client.close()


# 创建一个全局可复用的 ES 客户端管理器对象
es_client_manager = ESClientManager(app_config.es)


if __name__ == "__main__":
    # 先初始化客户端，后面的测试逻辑才能真正访问 ES
    es_client_manager.init()

    async def test():
        # 取出真正的 AsyncElasticsearch 客户端
        client = es_client_manager.client

        # 为了让示例可以反复运行，先删掉上次留下的同名索引
        # （ES 不允许创建同名索引，第二次直接 create 会抛 resource_already_exists_exception）
        if await client.indices.exists(index="my-books"):
            await client.indices.delete(index="my-books")

        # 创建索引
        # 这里同时显式定义了字段结构（≈ MySQL 的建表语句，字段类型见 mapping 的 type）
        # dynamic=False 表示关闭动态映射，要求写入数据必须符合当前定义
        # （不关的话，ES 遇到没声明的字段会自己猜类型，还可能顺手多建一份 keyword 子字段）
        await client.indices.create(
            index="my-books",
            mappings={
                "dynamic": False,
                "properties": {
                    # 书名和作者适合做全文检索，所以定义为 text：写入时按空格切词，查询时能模糊命中
                    "name": {"type": "text"},
                    "author": {"type": "text"},
                    # 日期字段按日期类型处理（format 声明了字符串里日期的写法）
                    "release_date": {"type": "date", "format": "yyyy-MM-dd"},
                    # 页数字段按整数处理
                    "page_count": {"type": "integer"},
                },
            },
        )

        # 插入数据
        # bulk 采用“操作说明 + 数据本体”交替出现的格式：
        #   {"index": {"_index": "my-books"}}  ← 动作行，说明接下来这条要做什么
        #   {"name": ..., ...}                ← 数据行，要写入的文档本身
        # 两者在列表里成对出现，一次请求写入多条，比循环单条写省掉大量网络往返
        # refresh=True：写完立刻刷新索引，保证下面的 search 能立刻搜到；
        # 不加的话 ES 默认约 1 秒才刷新一次，紧接着搜索可能是 0 条结果（生产批量写入一般不加，强制刷新有代价）
        await client.bulk(
            operations=[
                {"index": {"_index": "my-books"}},
                {
                    "name": "Revelation Space",
                    "author": "Alastair Reynolds",
                    "release_date": "2000-03-15",
                    "page_count": 585,
                },
                {"index": {"_index": "my-books"}},
                {
                    "name": "1984",
                    "author": "George Orwell",
                    "release_date": "1985-06-01",
                    "page_count": 328,
                },
                {"index": {"_index": "my-books"}},
                {
                    "name": "Fahrenheit 451",
                    "author": "Ray Bradbury",
                    "release_date": "1953-10-15",
                    "page_count": 227,
                },
                {"index": {"_index": "my-books"}},
                {
                    "name": "Brave New World",
                    "author": "Aldous Huxley",
                    "release_date": "1932-06-01",
                    "page_count": 268,
                },
                {"index": {"_index": "my-books"}},
                {
                    "name": "The Handmaids Tale",
                    "author": "Margaret Atwood",
                    "release_date": "1985-06-01",
                    "page_count": 311,
                },
            ],
            refresh=True,
        )

        # 搜索
        # 在 name 字段上执行 match 查询，这里演示的是最基础的全文检索能力
        # match 会先用字段的分词规则处理查询词 "brave"，再和倒排索引里的词条比对，
        # 所以能命中 "Brave New World"（大小写不敏感也是分词环节的功劳）
        resp = await client.search(
            index="my-books",
            query={"match": {"name": "brave"}},
        )

        # 打印查询结果，便于观察 hits 和返回结构
        # （响应很长，重点看 hits.total.value 命中了几个，以及 hits.hits[]._source 里的原文）
        print(resp)

        # 测试结束后关闭客户端连接
        await es_client_manager.close()

    # 运行异步测试函数
    asyncio.run(test())
