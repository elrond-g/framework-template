# FAQ

## General

**Q: What is this project?**
A: A full-stack chatbot framework template with a FastAPI backend and React frontend, designed as a starting point for building conversational AI applications.

**Q: What LLM providers are supported?**
A: Any OpenAI-compatible API. Set `LLM_API_BASE_URL` and `LLM_API_KEY` in `.env`. Works with OpenAI, Azure OpenAI, local models via vLLM/Ollama, etc.

## Backend

**Q: How do I add a new API endpoint?**
A: Create a new controller directory under `application/controller/`, add VO and controller files, then register the router in `main.py`.

**Q: How do I switch from SQLite to PostgreSQL?**
A: Update `DATABASE_URL` in `.env` to a PostgreSQL connection string (e.g., `postgresql://user:pass@localhost:5432/dbname`) and install `psycopg2-binary`.

**Q: What is the domain layer (command/phrase/step)?**
A: A layered pattern for complex business logic:
- **Command**: business intent entry point
- **Phrase**: composes multiple atomic steps
- **Step**: single atomic operation (e.g., one LLM call)

**Q: Why mock responses?**
A: When `LLM_API_KEY` is empty, the system returns mock responses so you can develop and test the UI without an API key.

## Frontend

**Q: How do I change the frontend port?**
A: Edit `server.port` in `application-web/vite.config.js`.

**Q: How does API proxying work?**
A: Vite proxies `/api/*` requests to `http://localhost:8000` during development. In production, configure your reverse proxy (nginx) to route API requests to the backend.

## Troubleshooting

**Q: Backend won't start — ModuleNotFoundError**
A: Make sure you're running from the `application/` directory and have installed dependencies with `pip install -r requirements.txt`.

**Q: Frontend can't reach the API**
A: Ensure the backend is running on port 8000. Check the Vite proxy config in `vite.config.js`.
