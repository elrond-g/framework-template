# 运维手册

## 部署

### 后端

```bash
cd application
pip install -r requirements.txt
# 生产环境：使用 gunicorn/uvicorn 多 worker 启动
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 前端

```bash
cd application-web
npm install
npm run build
# 将 dist/ 目录用 nginx、caddy 或其他静态文件服务器托管
```

### 环境配置

将 `.env.example` 复制为 `.env` 并设置生产环境参数：

```
DEBUG=false
DATABASE_URL=postgresql://user:pass@host:5432/chatbot
LLM_API_KEY=sk-...
CORS_ORIGINS=["https://your-domain.com"]
```

## 数据库

- 默认：SQLite（基于文件，适合开发环境）
- 生产环境：推荐 PostgreSQL — 修改 `DATABASE_URL` 即可
- 数据表在应用启动时自动创建

### 数据库迁移

生产环境的表结构变更，建议集成 Alembic：

```bash
pip install alembic
alembic init alembic
# 在 alembic.ini 中配置 DATABASE_URL
alembic revision --autogenerate -m "变更描述"
alembic upgrade head
```

## 监控

- 健康检查：`GET /api/system/health`
- FastAPI 自动生成文档：`/docs`（Swagger）或 `/redoc`

## 日志

日志同时输出到控制台和 `application/logs/` 目录下的文件：

| 文件 | 内容 | 级别 |
|------|------|------|
| `logs/app.log` | 全量日志 | DEBUG（debug 模式）/ INFO（生产） |
| `logs/error.log` | 仅错误日志 | ERROR |

日志文件使用 RotatingFileHandler 自动轮转，相关配置项：

```env
LOG_DIR=logs              # 日志目录（相对于 application/）
LOG_MAX_BYTES=10485760    # 单文件最大 10MB
LOG_BACKUP_COUNT=5        # 保留 5 个历史文件
```

生产环境可将 `logs/` 目录挂载到持久化存储，或将 stdout 接入日志聚合服务。

## 安全清单

- [ ] 生产环境设置 `DEBUG=false`
- [ ] 将 `CORS_ORIGINS` 限制为前端域名
- [ ] 生产环境使用 HTTPS
- [ ] 将敏感信息存储在环境变量中，不要写入代码
- [ ] 使用生产级数据库（PostgreSQL、MySQL）

## LLM 深度思考配置

当使用支持深度思考的模型（如 Claude、DeepSeek）时，可通过以下配置项控制思考行为：

```env
LLM_ENABLE_THINKING=true        # 是否启用深度思考（默认：true）
LLM_THINKING_BUDGET_TOKENS=10000 # 思考内容最大 token 数（默认：10000）
```

启用后，LLM 请求会附带 `reasoning_effort`、`enable_thinking`、`thinking.budget_tokens` 参数。代理服务（如 new-api / one-api）会将这些参数转发给底层模型。

**注意事项**：
- 深度思考会增加响应时间和 token 消耗
- 不支持思考功能的模型会忽略这些参数
- 如需关闭，设置 `LLM_ENABLE_THINKING=false`
