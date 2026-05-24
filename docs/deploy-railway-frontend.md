# Deploy frontend to Railway

Railway hosts the **Next.js UI**. The FastAPI backend runs on **Render** — deploy that first via Blueprint ([deploy-api-render.md](./deploy-api-render.md)).

```
Browser  →  Railway (frontend)  →  Render (API)  →  Groq + Gemini
```

---

## Prerequisites

1. **API live on Render** — `GET https://travel-agent-api.onrender.com/health` returns `{"status":"ok"}`
2. **GitHub repo** — [github.com/thebanerjeecode-source/travel-agent](https://github.com/thebanerjeecode-source/travel-agent)
3. [Railway account](https://railway.com) (free trial / hobby plan)

---

## Step 1 — Create Railway project

1. Go to [railway.com/new](https://railway.com/new)
2. Choose **Deploy from GitHub repo**
3. Select **`thebanerjeecode-source/travel-agent`**
4. Railway may try to deploy the whole repo — we'll fix the root directory next

---

## Step 2 — Set root directory to `frontend`

1. Open your new service in Railway
2. Go to **Settings**
3. Under **Source**, set **Root Directory** to:
   ```
   frontend
   ```
4. Save — Railway will redeploy using the Next.js app in `frontend/`

---

## Step 3 — Environment variables

In **Variables**, add:

| Name | Value |
|------|--------|
| `NEXT_PUBLIC_API_URL` | `https://travel-agent-api.onrender.com` |

Use your actual Render API URL — **no trailing slash**.

Railway sets `PORT` automatically; Next.js `npm start` uses it.

Click **Redeploy** after adding variables (`NEXT_PUBLIC_API_URL` is baked in at build time).

---

## Step 4 — Generate public URL

1. Go to **Settings → Networking**
2. Click **Generate Domain**
3. You'll get a URL like:
   ```
   https://travel-agent-frontend-production.up.railway.app
   ```

---

## Step 5 — Update CORS on Render (API)

In **Render → travel-agent-api → Environment**, set:

```
ALLOWED_ORIGINS=https://travel-agent-frontend-production.up.railway.app,http://localhost:3000
```

Replace with your exact Railway domain. Then **Manual Deploy** the API on Render.

---

## Step 6 — Verify

1. Open your Railway URL
2. Click **Demo** or submit a trip with **Dry-run mode** checked
3. You should see the agent trace and a 5-day Japan itinerary

---

## Railway CLI (optional)

```bash
npm i -g @railway/cli
railway login
cd "/Users/shubho/Travel Agent/frontend"
railway link
railway variables set NEXT_PUBLIC_API_URL=https://travel-agent-api.onrender.com
railway up
railway domain
```

---

## Custom domain (optional)

1. Railway → **Settings → Networking → Custom Domain**
2. Add your domain and follow DNS instructions
3. Update Render `ALLOWED_ORIGINS`:
   ```
   ALLOWED_ORIGINS=https://yourdomain.com,https://your-app.up.railway.app,http://localhost:3000
   ```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| **Failed to fetch** | Wrong `NEXT_PUBLIC_API_URL` or missing Railway URL in `ALLOWED_ORIGINS` on Render |
| **Build fails** | Confirm **Root Directory** = `frontend` |
| **Works locally, not on Railway** | Redeploy after setting `NEXT_PUBLIC_API_URL` |
| **502 on Railway** | Check deploy logs; ensure `npm run build` succeeds |
| **Slow first API call** | Render free tier cold start (~30s) — normal |
| **Gemini quota errors** | Use dry-run for public demo |

---

## What not to deploy on Railway (frontend service)

Do **not** point Railway at the repo root for the UI — that would try to run Python. Always use root directory `frontend`.

The FastAPI app stays on **Render** (long-running requests, 30–90s planning runs).

---

## Checklist

- [ ] Render API live at `/health`
- [ ] Railway service root directory = `frontend`
- [ ] `NEXT_PUBLIC_API_URL` set on Railway
- [ ] Railway public domain generated
- [ ] `ALLOWED_ORIGINS` on Render includes Railway URL
- [ ] Dry-run demo works in browser
