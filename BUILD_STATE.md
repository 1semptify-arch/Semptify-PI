# Semptify-PI Build State

## Session — 2026-09-01 — Build local_script reference plugin and tests

### Task

- **Task ID:** `septify-pi-local-script-2026-09-01`
- **Scope:** Implement the first Semptify-PI reference plugin (`local_script`) and prove the API spec end-to-end against `mock_core`.

### What changed

- `local_script/__init__.py` — package init.
- `local_script/config.py` — Pydantic `PluginConfig`, load/save `config.json`, environment variable overlay.
- `local_script/client.py` — sync `SemptifyPluginClient` with methods for list, get, connect, me, download-url, upload-url, and complete-upload. Accepts an injected `httpx.Client` for testability.
- `local_script/semptify_plugin.py` — `local-plugin` CLI with subcommands.
- `tests/conftest.py` — resets `mock_core` in-memory token state and provides a `TestClient` fixture.
- `tests/test_local_script.py` — 8 pytest tests covering config, list, get, connect, me, download, upload/complete, and CLI connect.
- `BUILD_GUIDE.md` — added `pytest tests/ -q` verification command.

### Findings

- The local_script plugin round-trips cleanly against `mock_core`. The client proves the zero-transfer model: it never touches document bytes, only direct URLs and metadata.
- The CLI writes the plugin token to `local_script/config.json` after connect; the token is not logged.
- The `mock_core` spec appears sufficient for the local_script flow; no spec changes were needed.

### Verification

- `python -m py_compile local_script/__init__.py local_script/config.py local_script/client.py local_script/semptify_plugin.py tests/__init__.py tests/conftest.py tests/test_local_script.py`: PASS
- `pytest tests/ -v`: 8 passed
- Manual end-to-end against `uvicorn mock_core.main:app --port 9000`:
  - `local-plugin ... connect example-document-organizer`: OK
  - `local-plugin ... me`: OK
  - `local-plugin ... download-url doc_123`: OK
  - `local-plugin ... upload-url notice.pdf --parent-folder /Semptify5.0/Inbox`: OK
  - `local-plugin ... complete <completion_token> provider_abc notice.pdf --size 1024`: OK

---

## Session — 2026-08-30 — Configure local PostgreSQL 16 for agent use

### Task

- **Task ID:** `pi-local-postgres-config-2026-08-30`
- **Scope:** Wire Semptify-PI to the local PostgreSQL 16 instance on Brad's machine for agent/test use.

### What changed

- Created `semptify_pi` database and `semptify_pi` user on local PostgreSQL 16.
- Set `DATABASE_URL` in `.env` (gitignored) to the local `semptify_pi` database.
- Updated `.env.example` with the `DATABASE_URL` template and notes.
- Added `asyncpg` to `pyproject.toml` dependencies.
- Created `tools/verify_postgres.py` to confirm the agent can connect.
- Updated `AGENTS.md` with local Postgres notes.
- Updated `README.md` with repo structure and local database section.
- Created `BUILD_GUIDE.md` with setup and verification commands.
- Configured `pg_hba.conf` to `trust` for local `127.0.0.1/32` and `::1/128` connections only, because the existing `postgres` superuser password was unknown and this is a scratch/test instance with no production data.

### Verification

- `python -m py_compile tools/verify_postgres.py`: PASS.
- `python tools/verify_postgres.py`:
  - Output: `OK: connected to ServerVersion(major=16, minor=0, micro=14, releaselevel='final', serial=0)`
  - Output: `Result: 1`

### Notes

- The `postgres` superuser password remains unknown. `pg_hba.conf` uses `trust` for localhost only, so the agent can connect without a superuser password. This is acceptable for a local scratch instance with no tenant data.
- The real plugin directory on Render is separate and unaffected.
