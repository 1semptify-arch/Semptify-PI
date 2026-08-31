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
   ```

## Environment variables

| Variable | Purpose |
|---|---|
| `MOCK_CORE_HOST` | Host for the mock Core server. |
| `MOCK_CORE_PORT` | Port for the mock Core server. |
| `SEMPIFY_PI_PLUGIN_TOKEN` | Example plugin token for local testing. |
| `SEMPIFY_PI_CORE_URL` | URL of the Core instance the plugin talks to. |
| `DATABASE_URL` | Local PostgreSQL 16 for agent/tests. Example: `postgresql+asyncpg://semptify_pi:<password>@localhost:5432/semptify_pi` |

## Verification commands

- `python -m py_compile <file>` — compile check.
- `python tools/verify_postgres.py` — confirm Postgres connection.
- `pytest` — run tests once a `tests/` directory exists.

## Notes

- This repo is decoupled from Semptify Core. It has its own `DATABASE_URL` and does not share Core's database.
- The local Postgres `semptify_pi` database is for agent scratch work and testing only.
