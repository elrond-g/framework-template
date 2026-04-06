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
