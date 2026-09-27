```txt

shopkeeper-agent/
├─ main.py  # FastAPI 入口脚本，负责创建应用并注册路由
└─ app/
   ├─ api/
   │  ├─ routers/
   │  │  └─ query_router.py  # 查询接口路由，接收请求并返回流式响应
   │  ├─ schemas/
   │  │  └─ query_schema.py  # 查询接口请求体结构
   │  ├─ dependencies.py  # 查询接口依赖项，负责组装 QueryService
   │  └─ lifespan.py  # FastAPI 生命周期事件，负责初始化和关闭外部客户端
   └─ services/
      └─ query_service.py  # 查询接口核心业务逻辑，负责调用问数工作流

```
