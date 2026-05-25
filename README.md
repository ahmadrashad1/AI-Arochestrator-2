# AI Orchestrator SaaS

Production-oriented monorepo scaffold for an AI orchestration automation SaaS.

## Included

- `frontend/` - Next.js app router frontend
- `backend/` - FastAPI service for orchestration, auth, billing, and workers
- `shared/` - cross-service DTOs and schemas
- `infra/` - Docker, Kubernetes, and deployment assets
- `docs/` - architecture and build plan
- `scripts/` - bootstrap and migration helpers

## Status

This repository currently contains the production scaffold and the implementation plan. The next step is to build the MVP vertically, starting with authentication, tenant isolation, and one narrow automation workflow.

## Roadmap

See [docs/MILESTONE_ROADMAP.md](docs/MILESTONE_ROADMAP.md) for the concise milestone view of delivery.

## CI / CD

- GitHub Actions CI workflow runs backend tests and builds the frontend on push and PRs: `.github/workflows/ci.yml`.
- CD workflow builds and publishes the backend Docker image to GitHub Container Registry on pushes to `main`: `.github/workflows/cd.yml`.
- The CD workflow uses the built-in `GITHUB_TOKEN` so no extra secrets are required for GHCR pushes in typical setups. If you prefer a dedicated PAT, set `GHCR_TOKEN` and update the workflow.

## Local alert receiver

- Docker Compose includes a local Alertmanager webhook receiver at `http://localhost:5001/`.
- Received alerts are stored in `data/alert_notifications.db` (SQLite by default) and can be inspected with `GET /alerts`.
- Optional outbound forwarding is supported through these environment variables in `docker-compose.yml`:
	- `ALERT_WEBHOOK_SLACK_URL`
	- `ALERT_WEBHOOK_DISCORD_URL`
	- `ALERT_WEBHOOK_EMAIL_TO`
	- `ALERT_WEBHOOK_EMAIL_FROM`
	- `ALERT_WEBHOOK_SMTP_HOST`
	- `ALERT_WEBHOOK_SMTP_PORT`
	- `ALERT_WEBHOOK_SMTP_USERNAME`
	- `ALERT_WEBHOOK_SMTP_PASSWORD`
	- `ALERT_WEBHOOK_SMTP_USE_TLS`

Email forwarding needs a real SMTP provider. Fill the variables like this:

```text
ALERT_WEBHOOK_EMAIL_TO=you@yourdomain.com
ALERT_WEBHOOK_EMAIL_FROM=alerts@yourdomain.com
ALERT_WEBHOOK_SMTP_HOST=smtp.yourprovider.com
ALERT_WEBHOOK_SMTP_PORT=587
ALERT_WEBHOOK_SMTP_USERNAME=your-smtp-username
ALERT_WEBHOOK_SMTP_PASSWORD=your-smtp-password
ALERT_WEBHOOK_SMTP_USE_TLS=true
```

```powershell
curl.exe -s http://localhost:5001/alerts | ConvertFrom-Json
```

## Running the runtime with DB-backed repositories

- By default the application runs in the legacy in-memory mode used by fast local tests. To run the FastAPI runtime against the SQLAlchemy/SQLite database, set the environment variable `REPO_BACKEND=DB`.

- Quick start (create DB, seed, and run):

```powershell
Set-Location 'D:\AI-orchestrator-2'
# create DB tables and seed default tenants/users/workspaces
python backend/scripts/seed_db.py

# run the app (example):
REPO_BACKEND=DB uvicorn app.main:app --reload --reload-dir backend
```

- To run the integration tests against the DB-backed runtime (recommended for manual validation):

```powershell
Set-Location 'D:\AI-orchestrator-2'
$env:REPO_BACKEND = 'DB'
python -m pytest backend/app/tests/integration/test_workflow_create_run.py -q
```

Notes:
- The DB seed script uses `sqlite:///./ai_orchestrator.db` by default (see `backend/app/database/connection.py`). Change `DATABASE_URL` in `.env` to point at Postgres or another DB when needed.
- LLM access uses `XAI_API_KEY` for Grok/xAI. Put it in the repo-root `.env` file (copied from `.env.example`) or export it in your shell before starting the backend.
- LLM access uses `XAI_API_KEY` for Grok/xAI. Put it in the repo-root `.env` file (copied from `.env.example`) or export it in your shell before starting the backend.

CI/CD docs: see [docs/CI_CD.md](docs/CI_CD.md) for instructions on rotating the XAI key and configuring repository secrets used by GitHub Actions.
- For production use prefer request-scoped sessions or a `scoped_session` pattern instead of the long-lived session created by the runtime prototype.
