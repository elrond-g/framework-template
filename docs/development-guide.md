# Development Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

## Backend Setup

```bash
cd application
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
cp .env.example .env       # Edit .env with your config
python main.py
```

Backend runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

## Frontend Setup

```bash
cd application-web
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`. API calls are proxied to the backend via Vite config.

## Project Structure

```
application/
├── main.py                    # Entry point
├── config/settings.py         # pydantic-settings configuration
├── controller/                # HTTP layer (routers + VOs)
│   ├── chat/                  # Chat endpoints
│   └── system/                # System endpoints (health)
└── library/
    ├── base/                  # API response, exceptions
    ├── domain/                # Domain-driven logic
    │   ├── command/           # Business commands
    │   ├── phrase/            # Logic composition
    │   └── step/              # Atomic operations
    ├── models/                # SQLAlchemy ORM models
    ├── managers/              # Data access layer
    └── services/              # Business services
```

## Layer Rules

1. **Controller** only imports from `services`
2. **Service** imports from `managers` and `domain/command`
3. **Command** only imports from `domain/phrase`
4. **Phrase** only imports from `domain/step`
5. **Step** performs atomic operations (API calls, tool invocations)

## Adding a New Feature

1. Define request/response VOs in `controller/<domain>/<domain>_vo.py`
2. Create or update the controller in `controller/<domain>/<domain>_controller.py`
3. Implement business logic in `library/services/<domain>_service.py`
4. If complex logic is needed, create domain layers under `library/domain/`
5. If data persistence is needed, add models in `library/models/` and managers in `library/managers/`

## API Response Format

All endpoints return a unified response:

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- `code: 0` = success
- `code: non-zero` = error (message explains)

## Environment Variables

See `.env.example` for all supported configuration keys. All settings are managed via `pydantic-settings` and can be overridden through environment variables or the `.env` file.
