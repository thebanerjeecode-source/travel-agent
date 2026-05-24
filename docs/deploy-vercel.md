# Deploy to Vercel (frontend)

Vercel hosts the **Next.js UI only**. The FastAPI backend must run on **Render** first — use the Blueprint in `render.yaml` ([deploy-api-render.md](./deploy-api-render.md)).

```
Browser  →  Vercel (frontend)  →  Render/Railway (API)  →  Groq + Gemini
```

---

## Prerequisites

1. **API deployed via Render Blueprint** — `GET https://travel-agent-api.onrender.com/health` returns `{"status":"ok"}`
2. **GitHub account** (easiest) or [Vercel CLI](https://vercel.com/docs/cli)
3. **Node.js 18+** locally if using the CLI

---

## Option A — GitHub + Vercel dashboard (recommended)

### 1. Push the repo to GitHub

```bash
cd "/Users/shubho/Travel Agent"
git init
git add .
git commit -m "Initial commit — travel planner with web UI"
git branch -M main
git remote add origin https://github.com/YOUR_USER/travel-agent.git
git push -u origin main
```

### 2. Import project on Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. **Import** your GitHub repository
3. Configure the project:

| Setting | Value |
|---------|--------|
| **Framework Preset** | Next.js (auto-detected) |
| **Root Directory** | `frontend` ← **important** |
| **Build Command** | `npm run build` (default) |
| **Output Directory** | *(leave default — do not set `.next` manually)* |
| **Install Command** | `npm install` (default) |

### 3. Set environment variables

In **Project → Settings → Environment Variables**, add:

| Name | Value | Environments |
|------|--------|--------------|
| `NEXT_PUBLIC_API_URL` | `https://your-api.onrender.com` | Production, Preview, Development |

Use your real Render/Railway API URL — **no trailing slash**.

Click **Deploy**.

### 4. Allow CORS on the API

After Vercel gives you a URL (e.g. `https://travel-agent-abc.vercel.app`), update the **API** env on Render:

```
ALLOWED_ORIGINS=https://travel-agent-abc.vercel.app
```

Redeploy the API service on Render so CORS picks up the new origin.

### 5. Verify

1. Open your Vercel URL
2. Go to **Demo** or submit a request with **Dry-run mode** checked
3. You should see the agent trace and a 5-day Japan itinerary

If the UI loads but requests fail with a network/CORS error, double-check `ALLOWED_ORIGINS` on the API matches your Vercel URL exactly (including `https://`, no trailing slash).

---

## Option B — Vercel CLI (no GitHub)

```bash
# Install CLI once
npm i -g vercel

cd "/Users/shubho/Travel Agent/frontend"
npm install

# Link and deploy (follow prompts)
vercel

# Set API URL for production
vercel env add NEXT_PUBLIC_API_URL production
# paste: https://your-api.onrender.com

# Production deploy
vercel --prod
```

Then set `ALLOWED_ORIGINS` on your API to the URL Vercel prints (e.g. `https://travel-agent-xxx.vercel.app`).

---

## Custom domain (optional)

1. Vercel → **Project → Settings → Domains** → add your domain
2. Update API `ALLOWED_ORIGINS` to include the custom domain:
   ```
   ALLOWED_ORIGINS=https://yourdomain.com,https://travel-agent-abc.vercel.app
   ```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| **Failed to fetch** / network error | API not running, wrong `NEXT_PUBLIC_API_URL`, or CORS — check `ALLOWED_ORIGINS` |
| **Build fails on Vercel** | Confirm **Root Directory** is `frontend`, not repo root |
| **Works locally, not on Vercel** | Rebuild after setting `NEXT_PUBLIC_API_URL` — it's baked in at build time |
| **Live runs timeout** | Render free tier may sleep; first request can take ~30s. Dry-run is instant. |
| **Gemini quota errors** | Use dry-run for public demo; live runs need API keys on Render |

---

## What not to deploy on Vercel

The Python FastAPI app (`src/api/`) should **not** go on Vercel:

- Trip planning runs 30–90 seconds — exceeds typical serverless timeouts
- Needs persistent env vars for `GROQ_API_KEY` / `GEMINI_API_KEY`

Use **Render** or **Railway** for the API. See [deploy-api-render.md](./deploy-api-render.md).

---

## Checklist

- [ ] API live at `https://…/health` → `ok`
- [ ] Vercel project root = `frontend`
- [ ] `NEXT_PUBLIC_API_URL` set on Vercel
- [ ] `ALLOWED_ORIGINS` on API includes Vercel URL
- [ ] Dry-run demo works in browser
- [ ] (Optional) Live run with keys on Render
