# Quick Start

## 环境要求

| 依赖 | 最低版本 |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |

## 1. 启动后端

```bash
cd application

# 创建虚拟环境
python -m venv venv
source venv/bin/activate       # macOS / Linux
# venv\Scripts\activate        # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的配置（不填 LLM_API_KEY 也可运行，会返回 Mock 响应）

# 启动服务
python main.py
```

启动成功后：
- API 服务：`http://localhost:8000`
- Swagger 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/system/health`

## 2. 启动前端

新开一个终端窗口：

```bash
cd application-web

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

打开浏览器访问 `http://localhost:5173`。

## 3. 开始对话

1. 点击左侧栏 **"+ New Chat"** 创建新会话
2. 在底部输入框输入消息，按 **Enter** 发送
3. 等待 AI 回复（未配置 API Key 时返回 Mock 响应）

> **Shift + Enter** 可在消息中换行。

## 4. 配置 LLM

编辑 `application/.env`：

```env
LLM_API_KEY=sk-your-api-key
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
```

支持任何 OpenAI 兼容接口（OpenAI、Azure OpenAI、Ollama、vLLM 等），修改 `LLM_API_BASE_URL` 即可切换。

修改后重启后端生效。

## 5. 切换数据库

默认使用 SQLite（自动创建 `chatbot.db` 文件）。切换 PostgreSQL：

```env
DATABASE_URL=postgresql://user:password@localhost:5432/chatbot
```

需额外安装驱动：

```bash
pip install psycopg2-binary
```

## 6. 验证安装

```bash
# 健康检查
curl http://localhost:8000/api/system/health

# 创建会话
curl -X POST http://localhost:8000/api/chat/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Test"}'

# 发送消息（替换 {id} 为上一步返回的会话 ID）
curl -X POST http://localhost:8000/api/chat/conversations/{id}/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

## 7. 生产构建

```bash
# 前端构建
cd application-web
npm run build
# 产出在 dist/ 目录，用 nginx 等静态服务器托管

# 后端生产启动
cd application
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 目录速览

```
framwork/
├── application/           # 后端 — Python / FastAPI
│   ├── main.py            # 入口
│   ├── config/            # 配置（pydantic-settings + .env）
│   ├── controller/        # 控制器层（HTTP 接口 + VO）
│   └── library/
│       ├── base/          # 基础工具（统一响应、异常处理）
│       ├── domain/        # 领域驱动层（command → phrase → step）
│       ├── models/        # ORM 模型（SQLAlchemy）
│       ├── managers/      # 数据访问层
│       └── services/      # 业务服务层
├── application-web/       # 前端 — React / Vite
└── docs/                  # 文档
```

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| `ModuleNotFoundError` | 确认在 `application/` 目录下运行，且已激活虚拟环境 |
| 前端无法调用 API | 确认后端在 8000 端口运行，检查 `vite.config.js` 代理配置 |
| LLM 无响应 | 检查 `.env` 中 `LLM_API_KEY` 和 `LLM_API_BASE_URL` 是否正确 |
