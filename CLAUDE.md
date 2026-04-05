# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language

本项目使用中文。所有文档、注释、commit message、PR 描述、代码中的用户可见文本均使用中文。变量名、函数名、类名等代码标识符使用英文。

## Documentation Sync

每次改动代码必须同步更新相关文档。涉及的文档包括但不限于：
- `README.md` — 项目说明、快速开始命令
- `docs/development-guide.md` — 开发手册（项目结构、层级规则、新增功能流程）
- `docs/user-guide.md` — 使用手册（功能说明、API 接口列表）
- `docs/operations-guide.md` — 运维手册（部署、配置、安全清单）
- `docs/quick-start.md` — 快速开始
- `docs/faq.md` — 常见问题

新增接口需更新 API 列表，修改配置项需更新 `.env.example` 和相关文档，变更架构需更新规划文档和开发手册。不允许代码已改但文档未同步的情况。

## Project Overview

Full-stack chatbot framework template: Python/FastAPI backend (`application/`) + React/Vite frontend (`application-web/`).

## Commands

### Backend
```bash
cd application
pip install -r requirements.txt
python main.py                          # starts uvicorn on :8000
```
API docs auto-generated at `http://localhost:8000/docs`.

### Frontend
```bash
cd application-web
npm install
npm run dev                             # starts vite dev server on :5173
npm run build                           # production build to dist/
```

Vite proxies `/api/*` to `http://localhost:8000` in dev mode.

## Architecture

### Backend Layer Hierarchy (strict call rules)

```
Controller → Service → Command → Phrase → Step
                    ↘ Manager (data access)
```

- **Controller** (`controller/<domain>/`): HTTP routers + Pydantic VOs. **Only calls Service.**
- **Service** (`library/services/`): Orchestrates business logic. Calls **Manager** for data and **Command** for complex logic.
- **Command** (`library/domain/command/`): Business intent entry. **Only calls Phrase.**
- **Phrase** (`library/domain/phrase/`): Composes atomic operations. **Only calls Step.**
- **Step** (`library/domain/step/`): Single atomic operations (LLM calls, external APIs).
- **Manager** (`library/managers/`): CRUD data access over SQLAlchemy models.
- **Models** (`library/models/`): SQLAlchemy ORM definitions.

**Never skip layers.** Controllers must not import domain or manager code directly. Commands must not call steps directly.

### Controller Convention

Each domain gets a subdirectory under `controller/` containing:
- `<domain>_controller.py` — FastAPI `APIRouter` with route handlers
- `<domain>_vo.py` — Pydantic request/response value objects

New routers must be registered in `main.py` via `app.include_router()`.

### Configuration

`config/settings.py` uses `pydantic_settings.BaseSettings` loading from `.env` file. All config accessed via the singleton `settings` instance. See `.env.example` for available keys.

### API Response Format

All endpoints return `ApiResponse[T]` (`library/base/api_response.py`):
```json
{"code": 0, "message": "success", "data": ...}
```
Use `ApiResponse.success(data=...)` and `ApiResponse.error(message=...)`. Custom exceptions (`AppException`) are caught by registered handlers and returned in this format.

### LLM Integration

`LLMStep` (`library/domain/step/llm_step.py`) calls OpenAI-compatible APIs via httpx. When `LLM_API_KEY` is empty, it returns mock responses — this is intentional for UI development without an API key.

### Frontend

React SPA with conversation sidebar + chat window. API calls go through `src/api/chat.js`. Components live in `src/components/`.
