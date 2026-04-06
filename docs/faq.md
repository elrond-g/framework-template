# 常见问题

## 综合

**问：这个项目是什么？**
答：一个八字命理测算 Web 应用，包含 FastAPI 后端和 React 前端。用户通过表单填写出生信息和测算方向，由 AI 八字大师角色进行命理分析。

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

**问：能否自定义测算方向？**
答：可以。除了预设的财运、事业、情感、健康、学业外，表单右侧有"其他方向"输入框，可以填写任意方向。

**问：提示词是如何生成的？**
答：前端表单填写后自动拼接为：`"你是一位精通八字的大师，帮我算一下出生于X年X月X日 X:X的X性，出生地是X，帮我算一下我的X。"`，作为用户消息发送给后端。

**问：如何修改前端端口？**
答：编辑 `application-web/vite.config.js` 中的 `server.port`。

**问：API 代理是如何工作的？**
答：开发环境下，Vite 将 `/api/*` 请求代理到 `http://localhost:8000`。生产环境需要配置反向代理（如 nginx）将 API 请求转发到后端。

## 错误处理

**问：后端异常类型有哪些？**
答：`AppException`（基础）、`NotFoundException`（404）、`ValidationException`（422）、`LLMException`（502）、`DatabaseException`（500）。详见开发手册中的错误处理规范。

**问：前端如何展示错误？**
答：API 客户端统一捕获错误并返回 `{code, message, data}` 格式。组件通过判断 `code !== 0` 展示错误提示条或错误消息气泡。

**问：LLM 调用失败时会发生什么？**
答：Step 层捕获 httpx 异常并抛出 `LLMException`。Service 层捕获后保存一条错误提示消息到会话中，然后继续抛出异常。前端会在聊天窗口中显示红色错误气泡。

## 故障排查

**问：后端无法启动，报 ModuleNotFoundError**
答：确认在 `application/` 目录下运行，并且已通过 `pip install -r requirements.txt` 安装依赖。

**问：前端无法连接 API**
答：确认后端正在 8000 端口运行，检查 `vite.config.js` 中的代理配置。
