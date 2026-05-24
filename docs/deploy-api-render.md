# Deploy API with Render Blueprint (`render.yaml`)

Use Render Blueprint to deploy the FastAPI backend from the `render.yaml` at the repo root. Do this **before** deploying the frontend to Railway.

---

## 1. Push to GitHub

Blueprint deploys from a Git repo. If you haven't already:

```bash
cd "/Users/shubho/Travel Agent"
git init
git add .
git commit -m "Travel planner — API + web UI"
git branch -M main
git remote add origin https://github.com/YOUR_USER/travel-agent.git
git push -u origin main
```

---

## 2. Create the Blueprint on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New +** → **Blueprint**
3. Connect your GitHub account and select the **travel-agent** repository
4. Render detects `render.yaml` and shows a preview of resources:

   | Resource | Name |
   |----------|------|
   | Web Service (Python) | `travel-agent-api` |

5. Click **Apply**

---

## 3. Enter secret environment variables

During Blueprint setup, Render prompts for variables marked `sync: false`:

| Variable | Required for dry-run? | What to enter |
|----------|----------------------|---------------|
| `ALLOWED_ORIGINS` | Yes (after Railway) | Start with `http://localhost:3000` — update to your Railway URL later |
| `GROQ_API_KEY` | No | Your Groq key (needed for live planning) |
| `GEMINI_API_KEY` | No | Your Gemini key (needed for live budget/validation) |
| `API_SECRET` | No | Optional shared secret for POST requests |

**Dry-run demo only:** leave `GROQ_API_KEY` and `GEMINI_API_KEY` blank; set `ALLOWED_ORIGINS` to your eventual Railway URL (`*` is **not supported** — use exact origins comma-separated).

Example for local + Railway testing:
```
ALLOWED_ORIGINS=http://localhost:3000,https://your-app.up.railway.app
```

6. Confirm and wait for the first deploy (~2–5 min)

---

## 4. Verify the API

Your service URL will look like:
```
https://travel-agent-api.onrender.com
```

```bash
# Health check
curl https://travel-agent-api.onrender.com/health
# {"status":"ok"}

# Dry-run plan (no API keys needed)
curl -X POST https://travel-agent-api.onrender.com/api/v1/plans \
  -H "Content-Type: application/json" \
  -d '{"request":"Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples.","dry_run":true}'
```

OpenAPI docs: `https://travel-agent-api.onrender.com/docs`

---

## 5. Connect Railway frontend

On Railway, set:
```
NEXT_PUBLIC_API_URL=https://travel-agent-api.onrender.com
```

After Railway gives you a URL, update **Render → travel-agent-api → Environment**:

```
ALLOWED_ORIGINS=https://your-app.up.railway.app,http://localhost:3000
```

Trigger **Manual Deploy** on Render so CORS reloads.

Full Railway steps: [deploy-railway-frontend.md](./deploy-railway-frontend.md)

---

## What's in `render.yaml`

```yaml
services:
  - type: web
    name: travel-agent-api
    runtime: python
    plan: free
    buildCommand: pip install --upgrade pip && pip install -r requirements.txt
    startCommand: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
```

| Field | Purpose |
|-------|---------|
| `plan: free` | Free web service (spins down after idle) |
| `healthCheckPath: /health` | Render uptime monitoring |
| `autoDeploy: true` | Redeploy on every push to `main` |
| `sync: false` env vars | Secrets you enter in the dashboard, not in Git |

---

## Updating the Blueprint

Edit `render.yaml`, commit, and push to `main`. Render auto-deploys if `autoDeploy: true`.

To add env vars later: **Render dashboard → travel-agent-api → Environment → Add variable**, then redeploy.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build fails: `No module named 'src'` | Ensure repo root contains `src/`, `requirements.txt`, `render.yaml` |
| Build fails on pip | Check `requirements.txt`; Python version set via `PYTHON_VERSION=3.11.11` |
| CORS error from Railway | Add exact Railway URL to `ALLOWED_ORIGINS`, redeploy API |
| First request very slow | Free tier cold start (~30–60s) — normal |
| Live run fails | Add `GROQ_API_KEY` and `GEMINI_API_KEY` in Render Environment |
| 502 / timeout on live run | Planning can take 30–90s; upgrade plan or use dry-run for demos |

---

## Manual deploy (without Blueprint)

If you prefer not to use Blueprint: **New → Web Service**, same build/start commands as in `render.yaml`. Blueprint is recommended — infrastructure stays in Git.

---

## API on Railway (alternative)

If you prefer the API on Railway instead of Render, use the same start command:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```
Set root directory to repo root (not `frontend`). Use the Railway API URL as `NEXT_PUBLIC_API_URL` on the frontend service.
