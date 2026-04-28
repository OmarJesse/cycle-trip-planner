# Cycling Trip Planner Agent

Build an AI agent that helps a cyclist plan a multi-day bike trip through conversation.

Example input:

> “I want to cycle from Amsterdam to Copenhagen. I can do around 100km a day, prefer camping but want a hostel every 4th night. Traveling in June.”

## Tech stack
- **FastAPI** (API)
- **Pydantic** (validation)
- **Anthropic Claude** (LLM tool-use)
- **Mock tools** (we’re testing architecture, not external API integration)

## Project structure
- `src/api`: FastAPI app + `/chat` + in-memory state
- `src/agent`: prompts + Claude client + orchestration loop + planning utilities
- `src/tools`: typed tools + registry/dispatcher (mock implementations)
- `src/tests`: basic unit tests + chat flow smoke test

## Tools implemented
- **Required**:
  - `get_route`
  - `find_accommodation`
  - `get_weather`
  - `get_elevation_profile`
- **Optional (bonus)**:
  - `get_points_of_interest`
  - `check_visa_requirements`
  - `estimate_budget`

## Run locally
### 1) Create a virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Set environment variables
Create `.env` in repo root:

```bash
# Provider selection
LLM_PROVIDER="anthropic"   # anthropic | gemini | mock
LLM_MODEL="claude-sonnet-4-6"

# Keys (depending on provider)
ANTHROPIC_API_KEY="YOUR_KEY"
# GEMINI_API_KEY="YOUR_KEY"

# Runtime knobs
MAX_TOOL_ROUNDS="6"
MAX_TOKENS="900"
INCLUDE_STRUCTURED_PLAN="true"
```

### 4) Start the API

```bash
# Preferred:
uvicorn src.api.app:app --reload --port 8000
#
# Convenience alias (kept for simplicity):
# uvicorn main:app --reload --port 8000
```

Open docs at `http://127.0.0.1:8000/docs`.

## Run backend + frontend (two terminals)
### Terminal 1: Backend (FastAPI)

```bash
./backend.sh
```

### Terminal 2: Frontend (Streamlit)

```bash
./frontend.sh
```

Open `http://localhost:8501` and chat with the agent.

## One-command dev start
Runs backend + frontend together:

```bash
./dev.sh
```

## API
### POST `/chat` (alias for v1)
Request:

```json
{ "conversation_id": "optional", "message": "..." }
```

Response:

```json
{ "conversation_id": "...", "reply": "..." }
```

### POST `/api/v0/chat`
- Minimal request/response (`message` → `reply`).

### POST `/api/v1/chat`
- Supports optional `preferences` overrides and can return a structured `plan`:

```json
{
  "conversation_id": "optional",
  "message": "...",
  "preferences": {
    "nationality": "Canadian",
    "month": "June",
    "daily_km": 100,
    "lodging_preference": "camping",
    "hostel_every_n_nights": 4
  }
}
```

## Architecture decisions (1 page max)
- **Separation of concerns**: `src/api` handles HTTP + state; `src/agent` handles orchestration; `src/tools` encapsulates capabilities.
- **Tool registry**: tools are typed (Pydantic input/output) and invoked via a single dispatcher for consistent validation and errors.
- **Conversation state**: in-memory store keyed by `conversation_id` (simple for demo; easy to swap to Redis/DB).
- **Claude tool-use**: bounded loop that executes tool calls and feeds results back to Claude until a final response is produced.

## With more time
- Real integrations (routing/elevation/lodging/POIs) + caching and rate-limit handling.
- Better preference extraction + constraint handling (rest days, ferry avoidance, bike type, safety).
- Persisted state and export formats (PDF/GPX), plus richer budget + visa logic by country.

## Screen recording
- Record a full conversation from first request to final itinerary and add link here.