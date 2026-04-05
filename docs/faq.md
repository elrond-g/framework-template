# 常见问题

## 综合

**问：这个项目是什么？**
答：一个全栈聊天机器人框架模板，包含 FastAPI 后端和 React 前端，作为构建对话式 AI 应用的起点。

**问：支持哪些 LLM 提供商？**
答：支持任何 OpenAI 兼容的 API。在 `.env` 中设置 `LLM_API_BASE_URL` 和 `LLM_API_KEY` 即可。兼容 OpenAI、Azure OpenAI、通过 vLLM/Ollama 部署的本地模型等。

## 后端

**问：如何新增 API 接口？**
答：在 `application/controller/` 下创建新的控制器目录，添加 VO 和控制器文件，然后在 `main.py` 中注册路由。

**问：如何从 SQLite 切换到 PostgreSQL？**
答：在 `.env` 中将 `DATABASE_URL` 修改为 PostgreSQL 连接字符串（例如 `postgresql://user:pass@localhost:5432/dbname`），并安装 `psycopg2-binary`。

**问：领域层（command/phrase/step）是什么？**
答：一种用于处理复杂业务逻辑的分层模式：
- **Command**：业务意图入口
- **Phrase**：组合多个原子步骤
- **Step**：单个原子操作（例如一次 LLM 调用）

**问：为什么会返回 Mock 响应？**
答：当 `LLM_API_KEY` 为空时，系统返回 Mock 响应，便于在没有 API Key 的情况下开发和测试 UI。

## 前端

**问：如何修改前端端口？**
答：编辑 `application-web/vite.config.js` 中的 `server.port`。

**问：API 代理是如何工作的？**
答：开发环境下，Vite 将 `/api/*` 请求代理到 `http://localhost:8000`。生产环境需要配置反向代理（如 nginx）将 API 请求转发到后端。

## 故障排查

**问：后端无法启动，报 ModuleNotFoundError**
答：确认在 `application/` 目录下运行，并且已通过 `pip install -r requirements.txt` 安装依赖。

**问：前端无法连接 API**
答：确认后端正在 8000 端口运行，检查 `vite.config.js` 中的代理配置。
