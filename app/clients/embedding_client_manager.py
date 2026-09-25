# Embedding 客户端管理器：创建并复用指向本机 TEI 的 embedding 客户端。

import asyncio
from typing import Required, TypedDict, Unpack

from langchain.embeddings import init_embeddings
from langchain_core.embeddings import Embeddings
from pydantic import SecretStr

from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingInitKwargs(TypedDict, total=False):
    """init_embeddings 的参数表：补上库签名里 **kwargs: Any 丢掉的类型信息，供 pyright 检查。

    键名需与 langchain-openai 的 OpenAIEmbeddings 保持一致，升级依赖后要复核。
    """

    base_url: str
    api_key: SecretStr
    check_embedding_ctx_length: Required[bool]


def build_embeddings(model: str, **kwargs: Unpack[EmbeddingInitKwargs]) -> Embeddings:
    """创建指向本机 TEI 的 embedding 客户端（按 OpenAI 兼容协议接入）。"""
    return init_embeddings(f"openai:{model}", **kwargs)


class EmbeddingClientManager:
    def __init__(self, config: EmbeddingConfig):
        # 保存 Embedding 服务配置，供 init() 时组装服务访问地址使用
        self.config = config
        # 客户端在模块导入阶段先不立即创建，避免启动时就发起外部依赖连接
        self._client: Embeddings | None = None

    @property
    def client(self) -> Embeddings:
        # 断言让类型检查器收窄掉 None，同时把“忘记调用 init()”变成明确的报错
        assert self._client is not None, "Embedding 客户端尚未初始化，请先调用 init()"
        return self._client

    def _get_url(self):
        # 根据配置拼出 Embedding 服务地址
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        # 在应用启动阶段显式调用，完成真正的客户端初始化
        self._client = build_embeddings(
            self.config.model,
            base_url=f"{self._get_url()}/v1",  # TEI 的 OpenAI 兼容路由
            api_key=SecretStr("not-needed"),  # TEI 不校验 key，但该字段不能为空
            check_embedding_ctx_length=False,  # 说明见上方 TypedDict
        )


# 模块级单例，供其他模块按需复用同一个客户端管理器
embedding_client_manager = EmbeddingClientManager(app_config.embedding)


if __name__ == "__main__":
    # 本地调试入口：初始化客户端后执行一次最小化向量化调用
    embedding_client_manager.init()
    client = embedding_client_manager.client

    async def test():
        # 使用示例文本验证 Embedding 服务是否可正常响应
        text = "What is deep learning?"
        query_result = await client.aembed_query(text)
        print("向量维度:", len(query_result))
        # 正确配置下实测得到的参考值；改动参数后可对照它发现“静默算错”
        # [-0.005919582676142454, 0.005813124123960733, 0.018300632014870644]
        print("前 3 个值:", query_result[:3])

    # 运行调试测试
    asyncio.run(test())
