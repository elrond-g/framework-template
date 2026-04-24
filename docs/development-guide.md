# 开发手册

## 环境要求

- Python 3.11+
- Node.js 18+
- npm 或 yarn

## 后端启动

```bash
cd application
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
cp .env.example .env       # 编辑 .env 填入你的配置
python main.py
```

后端运行在 `http://localhost:8000`，API 文档在 `http://localhost:8000/docs`。

## 前端启动

```bash
cd application-web
npm install
npm run dev
```

前端运行在 `http://localhost:5173`，API 请求通过 Vite 配置代理到后端。

## 项目结构

```
application/
├── main.py                    # 入口文件
├── config/settings.py         # pydantic-settings 配置
├── controller/                # HTTP 层（路由 + VO）
│   ├── chat/                  # 聊天接口
│   └── system/                # 系统接口（健康检查）
└── library/
    ├── base/                  # API 响应封装、异常处理
    ├── domain/                # 领域驱动逻辑
    │   ├── command/           # 业务命令
    │   ├── phrase/            # 逻辑组合
    │   └── step/              # 原子操作
    ├── models/                # SQLAlchemy ORM 模型
    ├── managers/              # 数据访问层
    └── services/              # 业务服务层
```

## 层级调用规则

1. **Controller** 只能导入 `services`
2. **Service** 可导入 `managers` 和 `domain/command`
3. **Command** 只能导入 `domain/phrase`
4. **Phrase** 只能导入 `domain/step`
5. **Step** 执行原子操作（API 调用、工具调用）

## 新增功能流程

1. 在 `controller/<domain>/<domain>_vo.py` 中定义请求/响应 VO
2. 在 `controller/<domain>/<domain>_controller.py` 中创建或更新控制器
3. 在 `library/services/<domain>_service.py` 中实现业务逻辑
4. 如果涉及复杂逻辑，在 `library/domain/` 下创建领域层代码
5. 如果需要数据持久化，在 `library/models/` 添加模型，在 `library/managers/` 添加管理器
6. **在 `application/tests/` 下同步补充单元测试**（硬性要求，见下方"测试"章节）

## 测试

本项目使用 `pytest` 作为测试框架，所有代码改动必须同步补充或更新单元测试。

### 目录结构

```
application/
├── pytest.ini                      # pytest 配置（asyncio_mode=auto 等）
└── tests/
    ├── conftest.py                 # 公共夹具：内存 DB、TestClient、环境变量
    ├── test_base_api_response.py   # ApiResponse
    ├── test_base_exceptions.py     # 异常体系与全局处理器
    ├── test_models.py              # ORM 模型默认值/级联
    ├── test_conversation_manager.py # Manager 层 CRUD + 异常回滚
    ├── test_llm_step.py            # Step 层：mock 与真实 httpx 分支
    ├── test_domain_phrase_command.py # Phrase/Command 编排
    ├── test_chat_service.py        # Service 层编排与错误路径
    └── test_controllers.py         # Controller 层 FastAPI TestClient 集成
```

### 运行

```bash
cd application
pytest                                   # 全部
pytest tests/test_chat_service.py        # 单文件
pytest -k test_chat_stream               # 按名称筛选
pytest -x --tb=short                     # 遇首个失败即停，简短堆栈
```

### 公共夹具（定义在 `tests/conftest.py`）

| 夹具 | 用途 |
|------|------|
| `db_engine` | 内存 SQLite 引擎（`StaticPool` 共享连接），自动建表/拆表 |
| `db_session` | 基于 `db_engine` 的 `Session`，用于 Manager/Service 测试 |
| `client` | `TestClient`，已通过 `dependency_overrides` 将 `get_db` 替换为内存 DB |

夹具在模块导入前会把 `LLM_API_KEY` 置空、`DATABASE_URL` 指向内存库，避免污染真实 `chatbot.db`。

### 各层测试约束

| 层 | 测试要点 |
|----|----------|
| `base/` | 数据结构 + 异常体系的行为；用最小 FastAPI app 验证全局处理器 |
| `models/` | 默认值、关系、级联删除 |
| `managers/` | 正常路径 + `SQLAlchemyError` 回滚路径（用 `monkeypatch` 注入失败 commit） |
| `domain/step/` | Mock 分支走真实代码；真实分支用 `httpx.MockTransport` 拦截 HTTP，覆盖超时/连接错误/5xx/JSON 异常 |
| `domain/phrase/` & `command/` | 使用 `unittest.mock.AsyncMock` 隔离下层，单独验证本层组装逻辑 |
| `services/` | 用 `AsyncMock` 替换 `chat_command.execute` / `execute_stream`，验证业务编排 + 错误半成品处理 |
| `controller/` | `TestClient` 打通整条链路，LLM 走 Mock 分支 |

### 硬性要求

- 新增函数/类 → 补 `test_*.py`
- 修 bug → 先写可复现的失败用例，再改代码，最后跑通
- 新增接口 → 在 `tests/test_controllers.py` 中补用例
- Manager 新增查询/写入 → 同时覆盖 `DatabaseException` 回滚路径
- Service 新增逻辑 → 覆盖成功路径与 `NotFoundException` / `LLMException` 失败路径
- 严禁为了让测试通过降低断言强度，也严禁在 CI 中 skip/xfail 掩盖问题

## 数据模型

### conversations 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `VARCHAR(36)` | UUID 主键 |
| `title` | `VARCHAR(255)` | 会话标题 |
| `system_prompt` | `TEXT`（可空） | 该会话的自定义系统提示词。`NULL` 表示使用 `library/domain/phrase/chat_phrase.py` 中的默认 `SYSTEM_PROMPT`。`ChatService` 在每次调用 LLM 前读取此字段作为 system prompt |
| `created_at` / `updated_at` | `DATETIME` | 时间戳 |

### SQLite 轻量迁移

本项目未引入 Alembic。`main.py` 的 `on_startup` 钩子在 `Base.metadata.create_all()` 之后会运行一次 `_migrate_conversations_add_system_prompt()`，对老版本 DB 幂等执行 `ALTER TABLE conversations ADD COLUMN system_prompt TEXT`。之后如需新增简单字段，可参照该函数追加迁移逻辑；若迁移复杂度提升，应引入 Alembic。

## API 响应格式

所有接口返回统一格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- `code: 0` = 成功
- `code: 非零` = 失败（message 字段说明错误原因）

## 错误处理规范

### 后端

项目使用分层错误处理机制，异常沿调用链向上传播，由全局异常处理器统一返回。

**异常类型**（定义在 `library/base/exceptions.py`）：

| 异常类 | 用途 | HTTP 状态码 |
|--------|------|------------|
| `AppException` | 基础业务异常 | 400 |
| `NotFoundException` | 资源不存在 | 404 |
| `ValidationException` | 参数校验失败 | 422 |
| `LLMException` | LLM 服务调用失败 | 502 |
| `DatabaseException` | 数据库操作失败 | 500 |

**各层职责**：

- **Step 层**：捕获外部调用异常（httpx 超时、连接失败、HTTP 错误、响应解析错误），转为 `LLMException` 抛出
- **Manager 层**：捕获 `SQLAlchemyError`，失败时执行 `db.rollback()`，转为 `DatabaseException` 抛出
- **Service 层**：捕获 `LLMException`，处理半成品状态（如用户消息已保存但 LLM 失败），然后继续抛出
- **Controller 层**：不做 try-catch，依赖全局异常处理器
- **全局异常处理器**：捕获所有 `AppException` 子类，按异常 code 映射 HTTP 状态码并返回统一格式

**日志**：

使用 `library/base/logger.py` 提供的统一 logger。各层在捕获异常时记录日志：

```python
from library.base.logger import logger

logger.error("描述: %s", str(exc))
logger.warning("业务警告: %s", message)
logger.info("操作记录: %s", detail)
```

**LLM 专用日志**：

`library/base/llm_logger.py` 提供 LLM 调用的专用日志，输出到 `logs/` 目录下两个独立文件：

| 文件 | 格式 | 用途 |
|------|------|------|
| `llm-digest.log` | 管道符分隔文本 | 摘要：打印时间、request_id、开始/结束时间、输入输出长度、TTFT、TOPT、成功/失败、失败原因 |
| `llm-describe.log` | JSONL（每行一个 JSON） | 详情：包含完整请求 messages 和返回内容，用于提示词调试 |

每次 `LLMStep.call_llm()` 调用（含 Mock 响应）都会自动写入这两个日志。字段说明：

- `request_id` — 8 位 UUID 短标识，用于关联同一请求的两条日志
- `ttft_ms` — Time To First Token（毫秒，非流式请求 = 总耗时）
- `topt` — 输出吞吐量（chars/s = 输出字符数 / 总耗时秒）
- `error_reason` — 失败原因（成功时为空）

### 前端

- **API 客户端**（`src/api/chat.js`）：统一捕获网络错误和 HTTP 错误，返回 `{code, message, data}` 格式，组件无需 try-catch
- **组件**：检查 `res.code === 0` 判断成功，失败时设置 `error` 状态展示提示
- **错误展示**：顶部错误提示条（App 级别）+ 聊天窗口内错误消息气泡（`role="error"`）

## 环境变量

参见 `.env.example` 获取所有支持的配置项。所有配置通过 `pydantic-settings` 管理，可通过环境变量或 `.env` 文件覆盖。
