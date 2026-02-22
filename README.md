# Cloudwalk Agent Swarm

## Mandatory configuration

Before starting the project, replace the API keys with your own valid values:

- `GOOGLE_API_KEY`
- `SERPER_API_KEY`
- `SLACK_WEBHOOK_URL`

Example in `.env`:

```env
GOOGLE_API_KEY="your_google_api_key"
SERPER_API_KEY="your_serper_api_key"
SLACK_WEBHOOK_URL="your_slack_webhook_url"
DATABASE_URL="postgresql://postgres:postgres@postgres:5432/cloudwalk"
MAX_INPUT_CHARS="2000"
MAX_TRANSFER_AMOUNT="20000"
```

You can create your `.env` from the example template:

### Linux/macOS
```bash
cp .env.example .env
```

### Windows (PowerShell)
```powershell
Copy-Item .env.example .env
```

## Run with Docker

### Linux/macOS
```bash
docker compose up --build
```

### Windows (PowerShell)
```powershell
docker compose up --build
```

## Access

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- Frontend (React): http://localhost:5173
- Postgres: localhost:5432
- Login endpoint: `POST /auth/login` with `{ "username": "Your Name" }`
- Transfer list endpoint: http://localhost:8000/customers/{user_id}/transfers

## Frontend flow

1. Open `http://localhost:5173`.
2. Sign in with your username.
3. The backend gets or creates a customer in Postgres with a generated id like `client001`.
4. Chat with the assistant.
5. Use **Transfer history** to open a popup with your sent/received transfers only.

## Structure (summary)

- `routers/`: defines the API HTTP routes.
- `services/`: business logic, including the PostgreSQL persistence layer.
- `utils/`: groups utilities, agents, factories, and supporting tools for the main flow.
- `frontend-react/`: React application (Vite + Nginx container).
- `chroma_infinitepay_db/`: stores the persisted data from the local vector database (Chroma).

## Youtube
[![Watch the video](https://img.youtube.com/vi/XHrRF0wb1CE/maxresdefault.jpg)](https://www.youtube.com/watch?v=XHrRF0wb1CE)
https://www.youtube.com/watch?v=XHrRF0wb1CE
