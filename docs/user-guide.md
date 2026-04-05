# User Guide

## Getting Started

1. Open your browser and navigate to `http://localhost:5173`
2. Click **"+ New Chat"** in the sidebar to create a conversation
3. Type your message in the input box and press **Enter** (or click **Send**)
4. The assistant will reply. Continue the conversation as needed.

## Features

### Conversations
- Create multiple conversations from the sidebar
- Switch between conversations by clicking on them
- Delete a conversation with the **x** button

### Chat
- Type messages and receive AI responses
- Message history is preserved per conversation
- Press **Shift+Enter** for a new line in your message

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/chat/conversations` | Create a new conversation |
| GET    | `/api/chat/conversations` | List all conversations |
| GET    | `/api/chat/conversations/{id}/messages` | Get conversation messages |
| POST   | `/api/chat/conversations/{id}/chat` | Send a message and get reply |
| DELETE | `/api/chat/conversations/{id}` | Delete a conversation |
| GET    | `/api/system/health` | Health check |

## Configuration

Edit the `.env` file in the `application/` directory to configure:

- `LLM_API_KEY` — Your LLM provider API key
- `LLM_MODEL` — Model to use (default: gpt-4)
- `DATABASE_URL` — Database connection string

Without an API key, the system returns mock responses for testing.
