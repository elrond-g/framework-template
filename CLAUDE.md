# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language

本项目使用中文。所有文档、注释、commit message、PR 描述、代码中的用户可见文本均使用中文。变量名、函数名、类名等代码标识符使用英文。

## Documentation Sync

每次改动代码必须同步更新相关文档。涉及的文档包括但不限于：
- `README.md` — 项目说明、快速开始命令
- `docs/development-guide.md` — 开发手册（项目结构、层级规则、新增功能流程、错误处理规范）
- `docs/user-guide.md` — 使用手册（功能说明、API 接口列表）
- `docs/operations-guide.md` — 运维手册（部署、配置、安全清单）
- `docs/quick-start.md` — 快速开始
- `docs/planning.md` — 项目规划
- `docs/faq.md` — 常见问题

新增接口需更新 API 列表，修改配置项需更新 `.env.example` 和相关文档，变更架构需更新规划文档和开发手册。不允许代码已改但文档未同步的情况。

## Project Overview

全栈对话式聊天机器人 Web 应用框架模板：Python/FastAPI 后端（`application/`）+ React/Vite 前端（`application-web/`）+ 文档（`docs/`）。

## Project Requirements

以下是本项目的完整需求规范，所有改动必须遵守这些约束：

### 目录结构

1. 项目根目录包含：`application/`（后端）、`application-web/`（前端）、`docs/`（文档）
2. 后端是 Python 项目，使用 FastAPI 作为 Web 服务框架，使用 Pydantic 实体类进行强类型约束
3. 后端目录包含 `controller/`、`library/`、`config/`、`requirements.txt`、`main.py`

### 后端子目录职责

- `controller/<domain>/` — 按业务分类的子目录，包含 controller 和 vo 文件
- `library/base/` — 基础依赖服务、API Kit 封装、日志、异常定义
- `library/domain/` — 领域驱动层，分为 `command/`、`phrase/`、`step/` 三层
- `library/models/` — ORM 映射层，使用 SQLAlchemy 框架
- `library/managers/` — 数据访问管理层
- `library/services/` — 业务逻辑代码
- `config/` — 配置文件，使用 `pydantic_settings` 管理，支持 `.env` 文件配置

### 层级调用规则（严格遵守，不可跨层调用）

```
Controller → Service → Command → Phrase → Step
                    ↘ Manager（数据访问）
```

1. **Controller** 只能调用 Service 层
2. **Service** 根据各类逻辑组装功能拼接结果；遇到复杂逻辑拆分到 domain 层，只能调用 Command 层
3. **Command** 负责命令入口，表达业务逻辑，只能调用 Phrase 层
4. **Phrase** 负责拼接原子动作组成业务逻辑，只能调用 Step 层
5. **Step** 负责拼接各种工具组成原子逻辑

### 错误处理

- 后端各层必须有完善的错误处理机制（异常捕获、日志记录、事务回滚）
- 前端 API 客户端统一捕获网络和 HTTP 错误，组件展示错误状态
- 异常类型：`AppException`、`NotFoundException`、`ValidationException`、`LLMException`、`DatabaseException`

### 前端

- 使用 React 框架，位于 `application-web/` 目录
- Vite 开发服务器代理 `/api/*` 到后端

### 文档

- `docs/` 目录包含：规划（`planning.md`）、开发手册（`development-guide.md`）、使用手册（`user-guide.md`）、运维手册（`operations-guide.md`）、快速开始（`quick-start.md`）、FAQ（`faq.md`）

### 其他

- 项目根目录包含 `.gitignore`（覆盖前后端）和 `README.md`（项目说明 + 快速开始命令）

## Commands

### Backend
```bash
cd application
pip install -r requirements.txt
python main.py                          # 启动 uvicorn，端口 :8000
```
API 文档自动生成在 `http://localhost:8000/docs`。

### Frontend
```bash
cd application-web
npm install
npm run dev                             # 启动 Vite 开发服务器，端口 :5173
npm run build                           # 生产构建输出到 dist/
```

Vite 开发模式下将 `/api/*` 代理到 `http://localhost:8000`。

## Architecture

### Controller Convention

每个业务域在 `controller/` 下有独立子目录，包含：
- `<domain>_controller.py` — FastAPI `APIRouter` 路由处理
- `<domain>_vo.py` — Pydantic 请求/响应 Value Objects

新路由必须在 `main.py` 中通过 `app.include_router()` 注册。

### Configuration

`config/settings.py` 使用 `pydantic_settings.BaseSettings` 从 `.env` 文件加载配置。通过单例 `settings` 访问。配置项参见 `.env.example`。

### API Response Format

所有接口返回 `ApiResponse[T]`（`library/base/api_response.py`）：
```json
{"code": 0, "message": "success", "data": ...}
```
使用 `ApiResponse.success(data=...)` 和 `ApiResponse.error(message=...)`。自定义异常由全局处理器捕获并以此格式返回。

### Error Handling

- 异常定义在 `library/base/exceptions.py`，日志在 `library/base/logger.py`
- Step 层捕获外部调用异常转为 `LLMException`
- Manager 层捕获 SQLAlchemy 异常，失败时 rollback 转为 `DatabaseException`
- Service 层捕获 `LLMException` 处理半成品状态
- 全局异常处理器按异常 code 映射 HTTP 状态码（404、422、500、502）

### LLM Integration

`LLMStep`（`library/domain/step/llm_step.py`）通过 httpx 调用 OpenAI 兼容 API。`LLM_API_KEY` 为空时返回 Mock 响应，用于无 API Key 的 UI 开发调试。

### Frontend

React SPA，左侧会话列表 + 右侧聊天窗口。API 调用通过 `src/api/chat.js`（统一错误处理）。组件在 `src/components/`。
