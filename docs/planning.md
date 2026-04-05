# 项目规划

## 概述

一个对话式聊天机器人 Web 应用框架，提供结构化的全栈项目模板，包含 Python/FastAPI 后端和 React 前端。

## 架构

### 调用层级

```
Controller → Service → Command → Phrase → Step
                    ↘ Manager（数据访问）
```

| 层级 | 职责 | 可调用 |
|------|------|--------|
| Controller | HTTP 接口、请求校验 | 仅 Service |
| Service | 业务编排 | Manager、Command |
| Command | 业务命令入口 | 仅 Phrase |
| Phrase | 组合原子操作 | 仅 Step |
| Step | 单个原子操作 | 外部 API / 工具 |
| Manager | 数据访问（CRUD） | ORM 模型 |

### 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python, FastAPI, Pydantic, SQLAlchemy |
| 前端 | React, Vite |
| 配置 | pydantic-settings + .env |
| 数据库 | SQLite（默认），支持所有 SQLAlchemy 兼容数据库 |

## 里程碑

- [ ] 阶段 1：核心框架模板
- [ ] 阶段 2：流式响应支持（SSE）
- [ ] 阶段 3：用户认证
- [ ] 阶段 4：多模型 LLM 支持
- [ ] 阶段 5：插件 / 工具调用系统
- [ ] 阶段 6：生产部署（Docker、CI/CD）
