# AI Travel Planner

Multi-agent trip planning system: parse natural-language requests into validated, day-by-day itineraries with lodging, logistics, and budget.

## Web UI (Phase 6)

Run the API and frontend locally:

```bash
# Terminal 1 — API
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Use **Dry-run mode** for offline demos without API keys.

### Docker (full stack)

```bash
docker compose up --build
# API: http://localhost:8000/docs
# UI:  http://localhost:3000
```

### API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/plans` | Create trip plan |
| `GET` | `/api/v1/plans/{id}` | Fetch stored plan |
| `GET` | `/api/v1/plans/{id}/markdown` | Download Markdown |

### Deploy

**API (Render Blueprint):** Commit `render.yaml` at repo root → Render **New → Blueprint** → connect GitHub.  
→ Full guide: **[docs/deploy-api-render.md](docs/deploy-api-render.md)**

**Frontend (Vercel):** Root directory `frontend/`, env `NEXT_PUBLIC_API_URL=https://travel-agent-api.onrender.com`.  
→ Full guide: **[docs/deploy-vercel.md](docs/deploy-vercel.md)**

After Vercel deploy, set `ALLOWED_ORIGINS` on the API to your Vercel URL and redeploy.

## Quick start (CLI)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys (copy and edit)
cp .env.example .env

# 3. Offline demo (zero API calls)
python3 -m src.main --dry-run \
  "Plan a 5-day trip to Japan. Tokyo + Kyoto. \$3,000 budget. Love food and temples, hate crowds." \
  --trace

# 4. Live run (Groq + Gemini)
python3 -m src.main \
  "Plan a 5-day trip to Japan. Tokyo + Kyoto. \$3,000 budget. Love food and temples, hate crowds." \
  --trace -m output/travel-itinerary.md
```

Open `output/travel-itinerary.md` in VS Code and press **Cmd+Shift+V** for a formatted preview.

## Architecture

Seven agents run in sequence:

```
Intent Parser (Groq)
  → Destination Research (Groq)
  → Itinerary Builder (Groq)
  → Accommodation (Groq)
  → Logistics (Groq)
  → Budget Analyst (Gemini)
  → Validator (Gemini)
```

| Brain | Agents | Provider |
|-------|--------|----------|
| Planning | Intent, Destination, Itinerary, Accommodation, Logistics | Groq |
| Review | Budget Analyst, Validator | Gemini |

Phase 4 adds **seed data** and optional **OpenTripMap** for Tokyo/Kyoto with traceable provenance.

## CLI reference

```bash
python3 -m src.main "Your trip request..." [OPTIONS]
```

| Flag | Description |
|------|-------------|
| *(default)* | Readable text itinerary on stdout |
| `--json` | JSON trip plan on stdout |
| `--trace` | Agent execution log + quota usage (stderr) |
| `-o FILE` | Save full JSON (plan + trace + quota) |
| `-m FILE` | Save Markdown itinerary (default: `output/travel-itinerary.md`; use `none` to skip) |
| `--dry-run` | Offline stub pipeline — **zero API calls** |
| `--stub` | Alias for `--dry-run` |
| `--intent-only` | Parse requirements only (1 Groq call) |
| `--planning-only` | Skip budget/validation (saves Gemini quota) |
| `--data-mode` | `auto` (default), `seed`, or `live` |

## Example scripts

```bash
./examples/japan_5day.sh    # Canonical Japan demo (dry-run)
./examples/jaipur_4day.sh   # Jaipur scenario
./examples/europe_10day.sh  # Europe multi-city
```

## Environment variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GROQ_API_KEY` | Live runs | — | Planning agents |
| `GEMINI_API_KEY` | Live runs | — | Budget + Validator |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Override Groq model |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Override Gemini model |
| `DATA_MODE` | No | `auto` | `seed` / `live` / `auto` |
| `OPENTRIPMAP_API_KEY` | No | — | Live POI data (Phase 4) |
| `ALLOWED_ORIGINS` | API | `http://localhost:3000` | CORS origins (comma-separated) |
| `API_SECRET` | No | — | Optional header auth for POST `/api/v1/plans` |

See `.env.example` for rate-limit defaults.

## API quota (typical live run)

| Provider | Calls per trip | Daily limit (free tier) |
|----------|----------------|-------------------------|
| Groq | 5–7 | ~1,000 RPD |
| Gemini | 2–4 | **20 RPD** |

Use `--dry-run` or `--planning-only` to conserve Gemini quota during development.

## Project layout

```
src/
  agents/          # Multi-agent pipeline
  api/             # Phase 6 FastAPI layer
  data/            # Phase 4 seed + live providers
  llm/             # Groq + Gemini clients, rate limiter
  orchestrator.py  # Pipeline routing + revision loops
  render/          # Markdown + terminal output
  main.py          # CLI entry point
frontend/          # Phase 6 Next.js web UI
data/seeds/        # Tokyo, Kyoto seed catalogs
prompts/           # Agent system prompts
examples/          # Demo scripts
tests/             # Unit + e2e tests
docs/              # Architecture, implementation plan
```

## Tests

```bash
# All tests (offline, no API)
pytest tests/ -q

# E2E + CLI only
pytest tests/test_e2e.py -v
```

## Deliverables (problem statement)

- Day-by-day trip outline
- Suggested neighborhoods / areas to stay
- Travel logistics between cities
- Budget breakdown with savings suggestions
- Validated final itinerary respecting preferences

## Docs

- [Problem statement](docs/problemStatement.md)
- [Architecture](docs/architecture.md) — agents, Trip Context, **§13–15 frontend & deploy**
- [Implementation plan](docs/implementation-plan.md) — **Phase 6** build steps
- [Edge cases](docs/edgecase.md)

## Roadmap

Phases 0–6 are complete (CLI + web UI + deploy configs).

See [implementation-plan.md § Phase 6](docs/implementation-plan.md#phase-6--frontend--deployment-) for architecture details.
