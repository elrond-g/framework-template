# Operations Guide

## Deployment

### Backend

```bash
cd application
pip install -r requirements.txt
# Production: use gunicorn/uvicorn workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd application-web
npm install
npm run build
# Serve dist/ with nginx, caddy, or any static file server
```

### Environment Configuration

Copy `.env.example` to `.env` and set production values:

```
DEBUG=false
DATABASE_URL=postgresql://user:pass@host:5432/chatbot
LLM_API_KEY=sk-...
CORS_ORIGINS=["https://your-domain.com"]
```

## Database

- Default: SQLite (file-based, suitable for development)
- Production: PostgreSQL recommended — update `DATABASE_URL`
- Tables are auto-created on application startup

### Migration

For schema changes in production, integrate Alembic:

```bash
pip install alembic
alembic init alembic
# Configure alembic.ini with your DATABASE_URL
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Monitoring

- Health check: `GET /api/system/health`
- FastAPI auto-generated docs: `/docs` (Swagger) or `/redoc`

## Logging

Configure Python logging as needed in `main.py`. In production, pipe stdout to a log aggregator.

## Security Checklist

- [ ] Set `DEBUG=false` in production
- [ ] Restrict `CORS_ORIGINS` to your frontend domain
- [ ] Use HTTPS in production
- [ ] Store secrets in environment variables, not in code
- [ ] Use a production database (PostgreSQL, MySQL)
