# Fleeting

全栈对话式聊天机器人应用框架模板，基于 **FastAPI** 后端 + **React** 前端。

提供开箱即用的项目结构、分层架构和 LLM 集成，适合作为对话式 AI 应用的开发起点。

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3.11+, FastAPI, Pydantic, SQLAlchemy |
| 前端 | React 18, Vite |
| 配置 | pydantic-settings + .env |
| 数据库 | SQLite（默认），支持 PostgreSQL 等 |

## 快速开始

### 后端

```bash
cd application
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # 按需编辑配置
python main.py                  # 启动在 http://localhost:8000
```

### 前端

```bash
cd application-web
npm install
npm run dev                     # 启动在 http://localhost:5173
```

打开浏览器访问 `http://localhost:5173`，点击 **"+ New Chat"** 开始对话。

> 未配置 `LLM_API_KEY` 时返回 Mock 响应，可直接用于 UI 开发调试。

## 项目结构

```
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

## 文档

- [快速开始](docs/quick-start.md)
- [开发手册](docs/development-guide.md)
- [使用手册](docs/user-guide.md)
- [运维手册](docs/operations-guide.md)
- [项目规划](docs/planning.md)
- [常见问题](docs/faq.md)
