# Project Planning

## Overview

A conversational chatbot web application framework providing a structured full-stack template with a Python/FastAPI backend and React frontend.

## Architecture

### Call Hierarchy

```
Controller → Service → Command → Phrase → Step
                    ↘ Manager (data access)
```

| Layer      | Responsibility                     | Can Call          |
|------------|-----------------------------------|-------------------|
| Controller | HTTP interface, request validation | Service only      |
| Service    | Business orchestration            | Manager, Command  |
| Command    | Business command entry             | Phrase only       |
| Phrase     | Compose atomic operations          | Step only         |
| Step       | Single atomic operation            | External APIs/tools |
| Manager    | Data access (CRUD)                | ORM models        |

### Tech Stack

| Component | Technology             |
|-----------|----------------------|
| Backend   | Python, FastAPI, Pydantic, SQLAlchemy |
| Frontend  | React, Vite           |
| Config    | pydantic-settings + .env |
| Database  | SQLite (default), any SQLAlchemy-supported DB |

## Milestones

- [ ] Phase 1: Core framework template
- [ ] Phase 2: Streaming response support (SSE)
- [ ] Phase 3: User authentication
- [ ] Phase 4: Multi-model LLM support
- [ ] Phase 5: Plugin / tool-use system
- [ ] Phase 6: Production deployment (Docker, CI/CD)
