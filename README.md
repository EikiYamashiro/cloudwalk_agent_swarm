# Cloudwalk Agent Swarm

## Solution architecture
Architecture diagram file: `img/cloudwalk_architecture.drawio.png`

![Cloudwalk solution architecture](img/cloudwalk_architecture.drawio.png)

### Customer Support Agent tools

The Customer Support Agent uses 2 tools:

- `get_customer_support_snapshot()`: reads customer profile and recent activity in a single diagnostic tool.
- `send_slack_message(message)`: escalates to human support using the current request user context.

### Knowledge Agent tools

The Knowledge Agent uses retrieval and web search:

- `retriever` + `format_context(...)`: retrieves and formats relevant InfinitePay context from the vector database (RAG path).
- `google_web_search(question)`: fallback for general questions when relevant RAG context is not found.

### Transfer Agent tools

The Transfer Agent uses 3 tools:

- `get_last_transfer()`: returns the latest transfer from the current request user.
- `get_transfers_from_user()`: returns the full transfer history from the current request user.
- `transfer(amount, counterparty_name)`: creates a new transfer for the current request user.

## Configuration

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

## Testing

Current automated tests are unit tests focused on deterministic logic:

- Guardrail input and transfer validation (`tests/test_guardrail_service.py`).
- Customer support tools behavior and response formatting (`tests/test_customer_support_tools.py`).

Run tests with:

```bash
pytest tests -q
```

## Integration testing strategy

For broader confidence in the swarm, the next step is integration tests with Docker Compose:

1. Start API + Postgres in an isolated test environment.
2. Seed test customers and transfers in Postgres.
3. Call `/message` scenarios end-to-end and assert routing outcomes:
   - knowledge requests -> Knowledge Agent path
   - support incidents -> Customer Support path + Slack tool mock
   - transfer requests -> Transfer Agent path + database write/read
4. Mock external dependencies (`SERPER`, Slack webhook, LLM provider) to keep tests deterministic and fast.

## Router Agent evaluation

Latest confusion matrix:

![Router Agent confusion matrix](tests/results/router_agent_confusion_matrix_20260223_013302.png)

Latest metrics:

```json
{
  "metrics": {
    "accuracy": 0.9565217391304348,
    "precision": 0.9642857142857143,
    "recall": 0.9642857142857143,
    "f1_score": 0.9615384615384615,
    "labels": [
      "knowledge",
      "transfer",
      "customer_support",
      "block"
    ]
  },
  "total_cases": 23,
  "total_errors": 1
}
```

## Youtube
[![Watch the video](https://img.youtube.com/vi/XHrRF0wb1CE/maxresdefault.jpg)](https://www.youtube.com/watch?v=XHrRF0wb1CE)
https://www.youtube.com/watch?v=XHrRF0wb1CE
