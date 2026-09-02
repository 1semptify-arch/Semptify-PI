# Semptify-PI Build Guide

**Python:** 3.11.9 only. Match Semptify Core's Python mandate.

## Local setup

1. Clone or open `C:\master-repo\sources\app-semptify-pi`.
2. Copy `.env.example` to `.env` and fill in real values (`.env` is gitignored).
3. Verify the local PostgreSQL 16 connection:
   ```powershell
   python tools/verify_postgres.py
   ```
4. Run services from `apps.yaml`:
   ```powershell
   uvicorn mock_core.main:app --port 9000
   uvicorn core.main:app --port 9000 --env-file .env
   ```

## Environment variables

| Variable | Purpose |
|---|---|
| `MOCK_CORE_HOST` | Host for the mock Core server. |
| `MOCK_CORE_PORT` | Port for the mock Core server. |
| `SEMPIFY_PI_PLUGIN_TOKEN` | Example plugin token for local testing. |
| `SEMPIFY_PI_CORE_URL` | URL of the Core instance the plugin talks to. |
| `DATABASE_URL` | Local PostgreSQL 16 for agent/tests. Example: `postgresql+asyncpg://semptify_pi:<password>@localhost:5432/semptify_pi` |
| `SEMPIFY_PI_ENCRYPTION_KEY` | Fernet key for encrypting provider refresh tokens at rest. |
| `SEMPIFY_PI_GOOGLE_CLIENT_ID/SECRET` | Google Drive OAuth app credentials. |
| `SEMPIFY_PI_DROPBOX_CLIENT_ID/SECRET` | Dropbox OAuth app credentials. |
| `SEMPIFY_PI_ONEDRIVE_CLIENT_ID/SECRET` | Microsoft OneDrive OAuth app credentials. |

## Verification commands

- `python -m py_compile <file>` — compile check.
- `python tools/verify_postgres.py` — confirm Postgres connection.
- `pytest tests/ -q` — run the full test suite (local_script + mock_core + browser_extension).
- `ruff check mock_core local_script core tests` — lint.
- `mypy mock_core local_script core tests` — type check.
- `pip install -e .[dev]` — install dev dependencies (pytest, ruff, mypy).

### Browser extension Node tests

The browser extension JS client is tested from Python via `tests/test_browser_extension.py`, which runs `browser_extension/test-node.mjs` against a live `mock_core`. To run it by hand:

```powershell
uvicorn mock_core.main:app --port 9000
$env:CORE_URL="http://127.0.0.1:9000"
$env:SESSION_TOKEN="sess_test"
node browser_extension/test-node.mjs
```

## Conventions

`C:\master-repo\CONVENTIONS.md` is the master source of truth for keeping this
repo's build docs, hand-offs, and logs separate from Semptify Core's. The
automated `check_repo_bleed.py` guardrail runs in pre-commit to catch accidental
literal-string bleed.

## Notes

- This repo is decoupled from Semptify Core. It has its own `DATABASE_URL` and does not share Core's database.
- The local Postgres `semptify_pi` database is for agent scratch work and testing only.

## Render deployment (free tier)

1. Push the repo to GitHub (`1semptify-arch/Semptify-PI`).
2. In the Render Dashboard, create a new **Web Service** and select this repo.
3. Choose the **Free** instance type (512 MB RAM, 0.1 CPU).
4. Render will read `render.yaml`; confirm:
   - **Build command:** `pip install -e .`
   - **Start command:** `uvicorn core.main:app --host 0.0.0.0 --port $PORT`
   - **Health check path:** `/health`
5. Set the secret environment variables in the Render Dashboard:
   - `DATABASE_URL` — the deployed Postgres URL (Render Postgres free tier, or your own).
   - `SEMPIFY_PI_ENCRYPTION_KEY` — the Fernet key.
   - Google, Dropbox, and OneDrive client ID/secret and redirect URIs.
6. Add your custom domain (`plugins.semptify.org`) under the service's **Custom Domains**.
7. In Cloudflare, add a `CNAME` record from `plugins` to the Render `onrender.com` subdomain.
8. Wait for Render to issue the TLS certificate and verify the domain.

### Free-tier limits

- 750 free instance hours per month across the workspace.
- The service spins down after 15 minutes without traffic and takes ~1 minute to cold-start.
- No persistent disk, no SSH, no edge caching.
- Render may restart the service at any time.

### Cost guardrail

- Do **not** upgrade to Starter unless you explicitly decide to.
- Do **not** add a payment method to the workspace if the goal is to stay strictly free.
- Monitor the Render Dashboard **Usage** page for instance-hour consumption.
