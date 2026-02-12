# Cloudwalk Agent Swarm

## Mandatory configuration

Before starting the project, replace the API keys with your own valid values:

- `GOOGLE_API_KEY`
- `SERPER_API_KEY`

Example in `.env`:

```env
GOOGLE_API_KEY="your_google_api_key"
SERPER_API_KEY="your_serper_api_key"
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

### Linux
```bash
docker compose up --build
```

### macOS
```bash
docker compose up --build
```

### Windows (PowerShell)
```powershell
docker-compose up --build
```

## Access

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- Frontend (Streamlit): http://localhost:8501

## Structure (summary)

- `routers/`: defines the API HTTP routes, including the messages endpoint.
- `services/`: contains the business logic used by the agents and the application state.
- `utils/`: groups utilities, agents, factories, and supporting tools for the main flow.
- `chroma_infinitepay_db/`: stores the persisted data from the local vector database (Chroma).

## Youtube
[![Watch the video](https://img.youtube.com/vi/XHrRF0wb1CE/maxresdefault.jpg)](https://www.youtube.com/watch?v=XHrRF0wb1CE)
https://www.youtube.com/watch?v=XHrRF0wb1CE
