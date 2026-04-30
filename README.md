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
└── tests/                        # 68 tests including scripted multi-step orchestration + HTTP-level v1 chat
streamlit_app.py                  # Streamlit entrypoint
main.py                           # uvicorn entrypoint
```

## Diagrams

Three architecture diagrams live under [`docs/diagrams/`](docs/diagrams/) and are walked through in the screen recording:

- [`system-diagram.png`](docs/diagrams/system-diagram.png). Three-layer architecture, single composition root in `runtime.py`, swap points for the LLM provider, the conversation store, and the tool registry. Defends the claim that any of those is a one-file change.
- [`chat-diagram.png`](docs/diagrams/chat-diagram.png). Request lifecycle for `POST /api/v1/chat`: middleware order, Pydantic validation, `handle_turn` (deep copy, `exclude_unset & exclude_none` preference merge, active-preferences framing), and the global exception handler mapping to HTTP statuses.
- [`agent-loop-diagram.png`](docs/diagrams/agent-loop-diagram.png). The bounded tool-use loop in detail: every `stop_reason` branch, parallel `tool_use` dispatch in a single round, `tool_use_id` pairing on the `tool_result` side, and the five exit shapes (end_turn, max_tokens, defensive, round-limit, upstream_failure) with their HTTP status mappings.

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

All shell entrypoints live in [`scripts/`](scripts/) — install, dev, backend, frontend, tests.

### 1. Install

```bash
./scripts/install.sh
```

One-shot bootstrap: verifies Python ≥ 3.11, creates `.venv` (rebuilds it if an older Python was used), installs the project + dev extras, copies `.env.example` → `.env` if missing, and wires `core.hooksPath` so the pre-commit hook (step 5) is active. Idempotent — safe to re-run any time `requirements.txt`/`pyproject.toml` change. Runnable from any cwd.

<details>
<summary>Manual install (if you'd rather not run the script)</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

</details>

### 2. Configure

Edit the `.env` that `install.sh` created from [`.env.example`](.env.example) (already gitignored). The full set of supported variables, with defaults, looks like this:

```bash
# Provider + model
LLM_PROVIDER="anthropic"            # anthropic | mock | gemini (gemini not wired)
LLM_MODEL="claude-sonnet-4-6"
ANTHROPIC_API_KEY=""                # required when LLM_PROVIDER=anthropic
GEMINI_API_KEY=""

# Tool-use loop budget
MAX_TOOL_ROUNDS="12"
MAX_TOKENS="4096"
PROMPT_CACHE_ENABLED="true"         # see Architecture decisions / Prompt caching

# Rate limiter (per-IP fixed window)
RATE_LIMIT_ENABLED="true"
RATE_LIMIT_REQUESTS="60"
RATE_LIMIT_WINDOW_SECONDS="60"

# CORS
CORS_ALLOW_ORIGINS='["http://localhost:8501","http://127.0.0.1:8501"]'
```

For tests or an offline demo, set `LLM_PROVIDER="mock"` (no key needed). Conversation TTL and capacity, log-body cap, and every mock-tool tunable (route distance ranges, accommodation prices, POI categories, visa rules, and so on) are also env-overridable. See [`src/config/settings/`](src/config/settings/) for the full surface.

### 3. Start

```bash
./scripts/dev.sh        # FastAPI on :8000 + Streamlit on :8501
# or, run them separately:
./scripts/backend.sh    # FastAPI on :8000
./scripts/frontend.sh   # Streamlit on :8501
```

Open <http://localhost:8501>.

### 4. Run tests

```bash
./scripts/tests.sh                              # full offline suite
./scripts/tests.sh src/tests/test_gpx_export.py # any pytest args pass through
./scripts/tests.sh --live                       # opt-in live LLM smoke tests
```

68 offline tests run in <1s and cover: scripted multi-step tool-use (sequential + parallel + validation errors + max-tokens / max-rounds truncation), preference-change adaptation, end-to-end v1 chat over HTTP with a scripted provider (including the 502-on-upstream-failure path), GPX export (extractor + serializer + 404 paths), redaction middleware, rate limiting, request-id correlation, and the deterministic v0 plan builder — entirely offline, no API key required.

#### Live LLM smoke tests (opt-in, costs API credits)

Two `@pytest.mark.live` tests in [`test_live_llm_smoke.py`](src/tests/test_live_llm_smoke.py) hit the real Anthropic API and assert the system prompt's contract end-to-end:
1. A full happy-path turn returns `truncated=False`, `error=None`, calls `get_route`, and emits both the `## Trip summary` and `## Day-by-day` headings.
2. A follow-up turn changing `daily_km` produces a different plan and a `**What changed**` line, per the system prompt.

Skipped by default. `./scripts/tests.sh --live` sets `RUN_LIVE_LLM=1` and runs only the `live`-marked tests (requires `ANTHROPIC_API_KEY` in `.env`).

Assertions are **structural** (headings, tool names, truncation flags), not text-equality, so the tests are resilient to model non-determinism while still catching real regressions in the system prompt or tool definitions. They're meant for nightly / on-demand runs — not the pre-commit hook.

### 5. Pre-commit hook

Already enabled by `install.sh` (`core.hooksPath=.githooks`). Every `git commit` runs the full pytest suite and aborts the commit if anything fails. To enable manually after a non-script install:

```bash
git config core.hooksPath .githooks
```

### 6. Run with Docker (optional)

A two-container setup is wired up for parity with a deployed environment. The backend container runs the FastAPI app with a `/health`-based healthcheck; the frontend container waits for it before starting.

```bash
docker compose up --build       # backend on :8000, frontend on :8501
```

Both containers read the same `.env` at the repo root, so put `ANTHROPIC_API_KEY` there before bringing the stack up. The frontend container uses `BACKEND_URL=http://backend:8000` so it talks to the backend on the compose network rather than `localhost`. See [`Dockerfile`](Dockerfile) and [`docker-compose.yml`](docker-compose.yml) for the exact build steps and healthcheck wiring.

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

### `GET /api/v1/conversations/{conversation_id}/route.gpx`

Exports the most recent `get_route` waypoints from the conversation's history as a GPX 1.1 file (`application/gpx+xml`) ready to import into Strava, Komoot, or any standard cycling app. Returns `404` if the conversation doesn't exist or no route has been planned yet. The endpoint reads directly from the conversation's tool-call history — no extra state to maintain. Note: while the mock `get_route` returns hash-based coordinates, this endpoint will produce a real, valid GPX file once a real routing API replaces the mock.

### `GET /health`
Liveness probe; returns provider/model in use.

### `POST /api/v1/tools/<name>`
Raw, single-call access to any registered tool, validated by the same Pydantic input/output schemas the agent uses. Available endpoints: `get_route`, `find_accommodation`, `get_weather`, `get_elevation_profile`, `get_points_of_interest`, `check_visa_requirements`, `estimate_budget`. Useful for debugging, integration testing, and consumers that want a specific tool without driving the chat loop.

### `POST /api/v0/chat` and `POST /api/v0/tools/<name>`
Deterministic, no-LLM endpoints. `chat` asks for missing preferences and assembles a plan directly from the tool registry. The `/tools/<name>` endpoints expose every tool (route, accommodation, weather, elevation, POI, visa, budget) for raw access. Useful as a fallback, for load testing, and for tool-only consumers. `POST /api/v0/tools/route.gpx` is a stateless GPX variant of `get_route`: same input shape, returns `application/gpx+xml` instead of JSON.

The split is intentional: **v1 is the AI agent surface** (chat with the agent calling tools internally, plus raw tool POSTs that share the registry); **v0 is the raw/deterministic surface** (direct tool access + a no-LLM chat that uses the deterministic plan builder). Both versions share the exact same `ToolRegistry`, so behavior never diverges.

Auto-generated OpenAPI schemas are served at `/docs` (Swagger UI) and `/redoc`. Every request gets an `X-Request-Id` correlation header echoed back in the response (see Production hygiene below).

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

### System prompt as a versioned artifact
The system prompt lives in [`src/agent/prompts/system.md`](src/agent/prompts/system.md), not as a string literal in code. That makes it diffable, reviewable, and testable. The "Hard rules" block (no deferral text, never fabricate tool outputs, always emit every day in full, round-budget awareness, never re-ask for fields in the active-preferences block) is the agent's behavior contract. The opt-in live LLM smoke tests assert this contract structurally (`## Trip summary`, `## Day-by-day`, and the `**What changed**` line on adaptation), so prompt regressions are caught the same way code regressions are.

### Active-preferences framing
Every user message sent to the LLM is augmented with an `[Active preferences ...]` block built from the merged `TripPreferences`. The system prompt declares that block authoritative, so the model never re-asks for fields the user has already given. Combined with `model_copy(deep=True)` and `exclude_unset=True, exclude_none=True` on the merge step, this gives the conversation turn-level atomicity: a turn that fails inside `handle_turn` does not corrupt the prior preferences in the store.

### Conversation state via a `Protocol`
[`ConversationStore`](src/state/base.py) is a Protocol with a single in-memory implementation today. Swapping to Redis / Postgres is one new class — no changes anywhere else. `ConversationState` carries the full Anthropic-shaped message history, so multi-turn refinements (e.g. "now make it 80 km/day") work without re-extracting context.

### Provider abstraction for testability
[`LLMProvider`](src/agent/providers/base.py) is a Protocol; `MockProvider` accepts a scripted response sequence so the orchestration loop is exercised in tests *without* an API key. `test_orchestration_loop.py` verifies multi-round tool dispatch, parallel tool calls, validation errors, and truncation — entirely offline.

### Config-driven, no magic numbers
Every tunable — model name, token budget, mock distance ranges, accommodation prices, POI categories, visa countries — lives in [`src/config/settings/`](src/config/settings/) (pydantic-settings, one file per concern, env-overridable). Tools call `get_settings()`; nothing is hardcoded mid-file.

### Prompt caching
The system prompt and the last tool schema carry `cache_control: ephemeral` when `PROMPT_CACHE_ENABLED=true`. The Anthropic cache breakpoint is cumulative, so a single breakpoint on the final tool schema caches the entire tool list, not just that one entry. Both blocks are stable across turns, so cache hits are the common case rather than the exception. Toggleable so an A/B comparison is one env-var flip away. Wired in [`prompts/__init__.py`](src/agent/prompts/__init__.py) and [`tools/registry.py`](src/tools/registry.py).

### Production hygiene
- `RequestIdMiddleware` assigns each incoming request a correlation ID (from the `X-Request-Id` header if the caller supplies one, otherwise generated). It's exposed on `request.state.request_id`, echoed back as a response header, and included in the request/response log so a single line can be traced end-to-end.
- `RequestResponseLogMiddleware` logs request/response bodies (truncated, JSON-parsed when possible) with sensitive-key redaction (`authorization`, `x-api-key`, `*_api_key`, `token`, `bearer`, `secret`, `password`) and the `request_id` from the upstream middleware.
- `RateLimitMiddleware` is a per-IP fixed-window limiter, env-toggleable, with lazy eviction of expired windows so memory does not grow unbounded.
- Global FastAPI exception handlers map `LLMProviderError`, `ToolError`, and uncaught exceptions to clean JSON `{ "error": ..., "type": ... }` responses — no stack traces leak to clients.
- Provider failures inside the agent loop are caught and surfaced via `OrchestrationResult.error` with `upstream_failure=True`; the v1 chat endpoint translates that into a **HTTP 502** so monitoring / alerting keys on standard 5xx, while the partial tool-call audit trail is still returned in the body. `max_tokens` and `max_rounds` truncations stay HTTP 200 with `truncated=true` — they're successful turns, just incomplete.

## What I'd build with more time

- **Streaming responses** (SSE) so the UI shows tool calls and text incrementally — currently the user waits for the full turn.
- **Real integrations** for at least one tool (e.g. Brouter for routing, Open-Meteo for weather) with caching + circuit breakers, keeping mocks behind a feature flag for offline dev.
- **Conversation memory, in order of leverage.** The current store keeps the full Anthropic message history per conversation. For trip-planning that's fine at <20 turns, but tool-result blocks bloat history fast (one `get_route` is ~2 KB; three days of weather + elevation + accommodation pushes 10 KB+, all of which is replayed on every subsequent turn). I'd address this in four steps, cheapest-first — not "add Redis." (1) **Compact stale tool results** once a final plan has been emitted: the plan markdown *is* the compressed representation, so prior `tool_use` / `tool_result` pairs older than the last turn can be dropped from the replayed history. No LLM round-trip, no eval needed. (2) **Promote stable facts into structured state** by extending `TripPreferences` (bike type, fitness, ferry tolerance, rest-day cadence, daylight constraints) so they live outside the message history and survive compaction. Today only the trip basics are typed; everything else relies on prose recall. (3) **Rolling summary of older turns** triggered only past a threshold (e.g. >30 turns), with the summary itself a typed Pydantic field so it can be inspected and asserted on, not a free-form blob. (4) **Persistent backing store** (Redis first, Postgres if we need richer queries) — last, because it's a deployment story rather than a memory-quality story. The Protocol-based `ConversationStore` already makes this a one-class change. Anthropic's context-editing / memory-tool features are an implementation choice within step 3, not a separate step.
- **Stronger preference modeling** — bike type, fitness, ferry preferences, rest-day cadence, daylight constraints — extracted by Claude into a typed Pydantic schema rather than a single free-form `notes` field.
- **Export formats** beyond GPX — ICS (calendar), Komoot collections, Strava routes — all served from the same conversation history extractor pattern as `route.gpx`.
- **Eval harness** — a small set of golden conversations scored against an LLM-as-judge to track regressions on the system prompt and tool definitions.
- **Map view** in the UI rendering the route waypoints (`pydeck` or similar).
