# Cycling Trip Planner Agent

A conversational AI agent that helps cyclists plan multi-day bike trips. It asks clarifying questions, calls typed tools to gather route, terrain, weather, accommodation, POI, budget, and visa data, then assembles a day-by-day itinerary — and adapts when the user changes their preferences mid-conversation.

> _"I want to cycle from Amsterdam to Copenhagen. I can do around 100km a day, prefer camping but want a hostel every 4th night. Traveling in June."_

## Stack

- **Python 3.11+**, FastAPI, Pydantic v2
- **Anthropic Claude** with tool-use (default: `claude-sonnet-4-6`)
- **Streamlit** chat UI
- **Mock tools** (the case study explicitly tests architecture, not external integration)

## Project layout

```
src/
├── agent/
│   ├── runtime.py                # composes settings + provider + registry + store
│   ├── orchestration/
│   │   ├── loop.py               # bounded tool-use loop, returns structured result
│   │   ├── blocks.py             # content-block helpers (text / tool_use)
│   │   └── types.py              # OrchestrationResult, ToolInvocation
│   ├── v1/orchestrator.py        # LLM-driven turn handler (default)
│   ├── v0/orchestrator.py        # deterministic fallback (no LLM, used by /api/v0)
│   ├── providers/                # LLMProvider Protocol + Anthropic + Mock impls
│   ├── prompts/system.md         # system prompt (file, not string literal)
│   └── planning/                 # deterministic plan builder used by v0
├── tools/
│   ├── registry.py               # ToolSpec + ToolRegistry + dispatcher
│   ├── builtins.py               # registry composition
│   ├── names.py                  # ToolName StrEnum
│   ├── get_route.py
│   ├── get_elevation_profile.py
│   ├── get_weather.py
│   ├── find_accommodation.py
│   ├── get_points_of_interest.py
│   ├── check_visa_requirements.py
│   └── estimate_budget.py
├── api/
│   ├── app.py                    # FastAPI app factory + middleware + exception handlers
│   ├── models.py                 # ConversationState, TripPreferences, DayPlan
│   ├── schemas.py                # ChatRequest, ChatResponse, ToolCallView
│   ├── deps.py                   # get_runtime() dependency
│   ├── health.py                 # /health
│   ├── middleware/               # rate limit + request/response logging + redaction
│   ├── v0/                       # deterministic chat + per-tool POSTs
│   └── v1/                       # LLM-driven chat + per-tool POSTs
├── state/                        # ConversationStore Protocol + in-memory impl
├── config/settings/              # pydantic-settings, one file per concern, env-overridable
├── logger/logging.py             # logger factory (uvicorn.error child)
├── exception/                    # AgentError + LLMProviderError + handlers
├── ui/                           # Streamlit UI components
└── tests/                        # 54 tests including scripted multi-step orchestration + HTTP-level v1 chat
streamlit_app.py                  # Streamlit entrypoint
main.py                           # uvicorn entrypoint
```

## Tools implemented

| Tool | Required | Purpose |
|---|---|---|
| `get_route` | ✅ | Route between two points: distance, waypoints, suggested days |
| `find_accommodation` | ✅ | Camping / hostel / hotel near a location |
| `get_weather` | ✅ | Typical weather for a location and month |
| `get_elevation_profile` | ✅ | Elevation gain + difficulty rating between points |
| `get_points_of_interest` | bonus | Daily highlights (sights, food, bike shops, nature, museums) |
| `check_visa_requirements` | bonus | Visa note based on nationality + destination + stay days |
| `estimate_budget` | bonus | Trip budget given days, daily km, lodging style, food style |

Every tool has Pydantic input/output models and is dispatched through a single typed registry, so adding a new tool is one file plus one line.

## Run locally

### 1. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

Create `.env` (already gitignored):

```bash
LLM_PROVIDER="anthropic"
LLM_MODEL="claude-sonnet-4-6"
ANTHROPIC_API_KEY="your-key"

MAX_TOOL_ROUNDS="12"
MAX_TOKENS="4096"

CORS_ALLOW_ORIGINS='["*"]'
```

For tests / offline demo, set `LLM_PROVIDER="mock"` (no key needed).

### 3. Start

```bash
./backend.sh    # FastAPI on :8000
./frontend.sh   # Streamlit on :8501
# or, both at once:
./dev.sh
```

Open <http://localhost:8501>.

### 4. Run tests

```bash
pytest
```

54 tests run in <1s and cover: scripted multi-step tool-use (sequential + parallel + validation errors + max-tokens / max-rounds truncation), preference-change adaptation, end-to-end v1 chat over HTTP with a scripted provider (including the 502-on-upstream-failure path), redaction middleware, rate limiting, and the deterministic v0 plan builder — entirely offline, no API key required.

### 5. Enable the pre-commit hook (one-time, per clone)

```bash
git config core.hooksPath .githooks
```

After this, every `git commit` runs the full pytest suite and aborts the commit if anything fails.

## API

### `POST /api/v1/chat`

```json
{
  "conversation_id": "optional",
  "message": "Plan Amsterdam to Copenhagen, 100km/day, camping, June",
  "preferences": {
    "nationality": "Canadian",
    "month": "June",
    "daily_km": 100,
    "lodging_preference": "camping",
    "hostel_every_n_nights": 4
  }
}
```

Response:

```json
{
  "conversation_id": "...",
  "reply": "## Trip summary\n- Route: Amsterdam → ...",
  "tool_calls": [
    { "name": "get_route", "input": {...}, "output": {...}, "is_error": false },
    ...
  ],
  "rounds": 4,
  "truncated": false,
  "error": null
}
```

`tool_calls` is an audit trail of every tool invocation the agent made for that turn — useful for the UI's "agent steps" panel and for debugging.

### `GET /health`
Liveness probe; returns provider/model in use.

### `POST /api/v0/chat` and `POST /api/v0/tools/<name>`
Deterministic, no-LLM endpoints. `chat` asks for missing preferences and assembles a plan directly from the tool registry. The `/tools/<name>` endpoints expose every tool (route, accommodation, weather, elevation, POI, visa, budget) for raw access — useful as a fallback, for load testing, and for tool-only consumers.

The split is intentional: **v1 is the AI agent surface** (chat only, the agent calls tools internally); **v0 is the raw/deterministic surface** (direct tool access + a no-LLM chat). Both versions share the exact same tool registry.

## Architecture decisions

### Separation of concerns
Three layers, each with a single responsibility:
- `src/api/` — HTTP, validation, middleware. Knows nothing about Claude.
- `src/agent/` — system prompt, provider abstraction, tool-use loop, orchestrators. Knows nothing about HTTP.
- `src/tools/` — typed mock data sources behind a registry. Knows nothing about either.

The whole graph is wired by `src/agent/runtime.py` and exposed via FastAPI's dependency injection (`get_runtime()`). Swapping the LLM, the store, or any tool is a one-file change.

### Tool registry, not a hand-rolled `if name == "..."` switch
Every tool is a `ToolSpec(name, description, InputModel, OutputModel, handler)`. The registry produces both the JSON schemas Claude needs and the runtime dispatcher with Pydantic validation, with consistent error reporting (`ToolError`). Adding a tool: write the input/output models + handler, add one line to `builtins.py`, write a test.

### Bounded tool-use loop
[`run_agent_loop`](src/agent/orchestration/loop.py) calls Claude, executes any `tool_use` blocks (including parallel ones), feeds typed results back, and loops. Bounded by `MAX_TOOL_ROUNDS` to prevent runaway loops, with explicit handling for `max_tokens` truncation. Returns a structured `OrchestrationResult` (reply + tool_calls audit + rounds + truncation flag) — not just a string — so the API and UI can show the user *what* the agent did.

### LLM-driven planning, no Python heuristics
Earlier versions had regex-based preference extraction and post-hoc deterministic plan injection. Both were removed: they masked LLM bugs, undermined the multi-step reasoning the case is testing, and broke conversation state. The agent now genuinely plans by calling tools.

### Conversation state via a `Protocol`
[`ConversationStore`](src/state/base.py) is a Protocol with a single in-memory implementation today. Swapping to Redis / Postgres is one new class — no changes anywhere else. `ConversationState` carries the full Anthropic-shaped message history, so multi-turn refinements (e.g. "now make it 80 km/day") work without re-extracting context.

### Provider abstraction for testability
[`LLMProvider`](src/agent/providers/base.py) is a Protocol; `MockProvider` accepts a scripted response sequence so the orchestration loop is exercised in tests *without* an API key. `test_orchestration_loop.py` verifies multi-round tool dispatch, parallel tool calls, validation errors, and truncation — entirely offline.

### Config-driven, no magic numbers
Every tunable — model name, token budget, mock distance ranges, accommodation prices, POI categories, visa countries — lives in [`src/config/settings/`](src/config/settings/) (pydantic-settings, one file per concern, env-overridable). Tools call `get_settings()`; nothing is hardcoded mid-file.

### Production hygiene
- `RequestIdMiddleware` assigns each incoming request a correlation ID (from the `X-Request-Id` header if the caller supplies one, otherwise generated). It's exposed on `request.state.request_id`, echoed back as a response header, and included in the request/response log so a single line can be traced end-to-end.
- `RequestResponseLogMiddleware` logs request/response bodies (truncated, JSON-parsed when possible) with sensitive-key redaction (`authorization`, `x-api-key`, `*_api_key`, `token`, `bearer`, `secret`, `password`) and the `request_id` from the upstream middleware.
- `RateLimitMiddleware` is a per-IP fixed-window limiter, env-toggleable, with lazy eviction of expired windows so memory does not grow unbounded.
- Global FastAPI exception handlers map `LLMProviderError`, `ToolError`, and uncaught exceptions to clean JSON `{ "error": ..., "type": ... }` responses — no stack traces leak to clients.
- Provider failures inside the agent loop are caught and surfaced via `OrchestrationResult.error` with `upstream_failure=True`; the v1 chat endpoint translates that into a **HTTP 502** so monitoring / alerting keys on standard 5xx, while the partial tool-call audit trail is still returned in the body. `max_tokens` and `max_rounds` truncations stay HTTP 200 with `truncated=true` — they're successful turns, just incomplete.

## What I'd build with more time

- **Streaming responses** (SSE) so the UI shows tool calls and text incrementally — currently the user waits for the full turn.
- **Real integrations** for at least one tool (e.g. Brouter for routing, Open-Meteo for weather) with caching + circuit breakers, keeping mocks behind a feature flag for offline dev.
- **Persistent state** (Redis or Postgres) replacing the in-memory store, plus export formats (GPX, ICS).
- **Stronger preference modeling** — bike type, fitness, ferry preferences, rest-day cadence, daylight constraints — extracted by Claude into a typed Pydantic schema rather than a single free-form `notes` field.
- **Eval harness** — a small set of golden conversations scored against an LLM-as-judge to track regressions on the system prompt and tool definitions.
- **Map view** in the UI rendering the route waypoints (`pydeck` or similar).
