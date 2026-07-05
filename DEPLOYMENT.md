# Deployment guide

Backend (FastAPI + Postgres) on Render, frontend (React/Vite) on Vercel. Both have a free tier
suitable for this project; see the one caveat about Render's free Postgres at the end.

## 1. Postgres (Render)

1. Render dashboard, New > PostgreSQL.
2. Name it (e.g. `senus-board-report-db`), free plan, create.
3. Once it's up, copy the **Internal Database URL** shown on its page (starts with
   `postgres://...`). You'll paste this into the API service's `DATABASE_URL` in step 2 below.
   The app normalises `postgres://`/`postgresql://` to the `postgresql+asyncpg://` scheme it needs
   automatically (`app/core/config.py`), so paste it exactly as Render shows it, no editing needed.

## 2. API (Render)

This is a monorepo (the Dockerfile lives at `apps/api/Dockerfile` but needs a build context of the
repo root, to also copy in the real `data/` used to self-seed the database). Rather than hunting
for the right combination of dashboard fields, use the `render.yaml` Blueprint already committed at
the repo root, which declares this explicitly:

1. Render dashboard, **New** > **Blueprint**, connect this GitHub repo.
2. Render detects `render.yaml` and shows the one service it defines
   (`senus-board-report-api`, Docker runtime, `dockerfilePath: apps/api/Dockerfile`,
   `dockerContext: .`). Confirm to create it.
3. It'll prompt for the env vars marked `sync: false` in `render.yaml` (everything except
   `JWT_EXPIRE_MINUTES`, which has a fixed value already). Fill in:
   | Key | Value |
   | --- | --- |
   | `DATABASE_URL` | the Internal Database URL from step 1 |
   | `GEMINI_API_KEY` | your key from aistudio.google.com |
   | `JWT_SECRET` | a long random string, e.g. `python3 -c "import secrets; print(secrets.token_hex(32))"` |
   | `DEMO_USER_EMAIL` | e.g. `ceo@senus.com` |
   | `DEMO_USER_PASSWORD` | a password of your choice |
   | `WEB_ORIGIN` | leave as `http://localhost:5173` for now, come back and set it to the real Vercel URL after step 3 |
4. Deploy. First boot runs (see `apps/api/Dockerfile`'s `CMD`): `alembic upgrade head`, seeds the
   demo user, loads all three source documents, derives the MODELLED monthly split, then starts
   serving. Watch the deploy logs for `Uvicorn running on...` to confirm it reached the end
   cleanly; `Loaded N new facts...` lines confirm the data actually landed.
5. Note the service's public URL (`https://<name>.onrender.com`), the frontend needs it next.
6. Free-tier web services spin down after 15 minutes idle and take about a minute to wake back up
   on the next request; that first request after idle will just look slow, not broken.

If you already started creating a plain Web Service by hand (not via Blueprint) and hit
`failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory`, that
service didn't have the right build context; delete it and use the Blueprint flow above instead.

## 3. Frontend (Vercel)

1. Vercel dashboard, Add New > Project, import this GitHub repo.
2. **Root Directory**: `apps/web` (monorepo, so this must be set explicitly).
3. Framework preset: Vite (should be auto-detected once the root directory is set).
4. Environment variable: `VITE_API_URL` = the Render API URL from step 2.5, e.g.
   `https://senus-board-report-api.onrender.com` (no trailing slash).
5. Deploy. `apps/web/vercel.json` already rewrites every path to `index.html`, so client-side
   routes like `/dashboard/profitability` work on a direct visit or refresh, not just via in-app
   navigation.

## 4. Close the loop

Go back to the Render API service and set `WEB_ORIGIN` to the real Vercel URL from step 3
(`https://<your-project>.vercel.app`), then redeploy the API (Render redeploys automatically on an
env var change on most plans; trigger one manually if not). Without this the browser's CORS check
blocks every request from the deployed frontend to the deployed API, even though both are
individually reachable.

## 5. Verify

Visit the Vercel URL, sign in with `DEMO_USER_EMAIL`/`DEMO_USER_PASSWORD`, and check all five
sections load with real data and an AI insight. If the AI insight fails, check the Render logs for
Gemini's free-tier rate limit (20 requests/day for `gemini-2.5-flash`): the endpoint returns a
clean 503 in that case rather than a bare error.

## Caveat: Render's free Postgres expires

A free Render Postgres database expires 30 days after creation (14-day grace period after that
before deletion). Fine for demoing this project in the short term; for anything longer-lived,
upgrade the database to a paid plan before the 30 days are up.
