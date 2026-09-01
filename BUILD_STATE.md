# Semptify-PI Build State

## Session — 2026-09-01 — Phase 2 implementation: real Core token/containment layer

### Task

- **Task ID:** `pi-phase-2-core-oauth-implementation-2026-09-01`
- **Scope:** Begin the real Core implementation. Token model, containment, and the required condition tests for Brad's approval.

### What changed

- New `core/` package:
  - `core/config.py` — Core settings, token lifetimes, vault folder, provider OAuth env vars.
  - `core/database.py` — async SQLAlchemy engine + session factory.
  - `core/models.py` — `PluginManifest`, `PluginToken`, `ProviderToken`, `VaultFile`, plus `UTCDateTime` decorator.
  - `core/tokens.py` — token issue/validate/revoke and per-file tenant validation.
  - `core/capabilities.py` — provider capability generation with vault-path containment.
  - `core/oauth.py` — OAuth URL builders (not yet exchanging codes; Phase 3 credentials).
  - `core/seeding.py` — seed the reference plugin manifest.
  - `core/main.py` — FastAPI app with the full plugin API.
- `tests/test_core.py` — tests for the four Brad-mandated conditions:
  1. Token revocation is immediate (`test_revoke_token_rejected_next_use`).
  2. Per-file tenant validation (`test_per_file_tenant_validation`).
  3. Dropbox containment outside `/Semptify5.0/Inbox` is rejected.
  4. OneDrive containment outside the vault folder is rejected.
- `pyproject.toml` — added `sqlalchemy[asyncio]`, `aiosqlite`, `core` package, `pi-core` script.
- `apps.yaml` — added `core` service.
- `.env.example` — added Core token, vault folder, and provider OAuth placeholders.

### Verification

- `ruff check mock_core local_script core tests`: PASS
- `mypy mock_core local_script core tests`: PASS
- `python -m py_compile` on changed files: PASS
- `pytest tests/ -q`: **21 passed**

### Notes

- OAuth code exchange is not yet implemented — it requires Brad-registered provider credentials (Phase 3).
- Provider access tokens are still synthetic; real refresh/access token exchange and scoped provider calls are next.
- The real Core currently uses SQLite for in-memory tests; Postgres is configured for local/Render via `DATABASE_URL`.

---

## Session — 2026-09-01 — Phase 2 OAuth/token plan (approved with conditions)

### Task

- **Task ID:** `pi-phase-2-oauth-plan-2026-09-01`
- **Scope:** Write the Phase 2 design plan for real Core OAuth, token scoping, and the minimal plugin manifest registry. Stop at the plan; do not implement until Brad signs off.

### What changed

- `C:\master-repo\handoffs\pi-phase-2-core-oauth-2026-09-01.md` — full Phase 2 handoff, plus the 2026-09-01 decision record:
  - Google Drive `drive.file` approved.
  - Dropbox `files.content.read/write` + `files.metadata.read` approved with containment test.
  - OneDrive `Files.Read` + `Files.ReadWrite` approved with containment test and folder-of-record.
  - Plugin token lifetime: **90 days default**; 1-year browser extension allowed only after immediate-revocation and per-file-tenant tests pass.
- `BLUEPRINT.md` — Phase 2 marked as "approved with conditions."
- `BUILD_STATE.md` — this entry.

### Verification

- Decision record reviewed and incorporated into plan.
- No implementation code written; no tests added for Phase 2.

### Next step

- Create implementation branch and begin Phase 2 work, or continue with the parallel Review Desk improvements task.

---

# Semptify-PI Build State

## Session — 2026-09-01 — Build-system scaffold (CI, pre-commit, pyproject lock)

### Task

- **Task ID:** `pi-build-scaffold-2026-08-30`
- **Scope:** Put a test/lint safety net in place before Phase 2 (real OAuth/token work).

### What changed

- `pyproject.toml`:
  - Removed stale `desktop_app` package and `desktop-plugin` console script.
  - Added `project.optional-dependencies.dev` with `pytest`, `ruff`, `mypy`.
  - Added `tool.ruff` and `tool.mypy` config.
  - Updated comment about the browser extension being a Node/ESM package.
- `.github/workflows/ci.yml` — GitHub Actions workflow that runs compile, ruff, mypy, pytest, and the Node browser-extension tests against a live `mock_core`.
- `.pre-commit-config.yaml` — local pre-commit hooks for ruff, mypy, compile, and pytest.
- `BUILD_GUIDE.md` — updated verification commands.
- `README.md` — updated repo structure and status.
- `local_script/client.py` and `local_script/semptify_plugin.py` — fixed mypy `no-any-return` with `typing.cast`.
- `tests/conftest.py`, `tests/test_local_script.py`, `tests/test_browser_extension.py` — fixed ruff import order and mypy return types.

### Verification

- `pip install -e .[dev]`: OK
- `ruff check mock_core local_script tests`: PASS
- `mypy mock_core local_script tests`: PASS
- `python -m py_compile` on changed Python files: PASS
- `pytest tests/ -q`: **15 passed**
- Manual Node round-trip (`uvicorn` + `node browser_extension/test-node.mjs`): OK
- Pushed to `1semptify-arch/Semptify-PI`.

---

## Session — 2026-09-01 — Build browser_extension reference plugin (Phase 1)

### Task

- **Task ID:** `septify-pi-roadmap-2026-09-01` (Phase 1)
- **Scope:** Implement the second Semptify-PI reference plugin (`browser_extension`) against the confirmed provider-differentiated contract.

### What changed

- Added `browser_extension/` directory:
  - `manifest.json` — Manifest V3 extension descriptor with storage permission and host permissions for mock/real Core.
  - `api-client.mjs` — ES module client with `fetch` for list, get, connect, me, download-url, upload-url, complete-upload.
  - `popup.html`, `popup.css`, `popup.mjs` — minimal extension popup UI that stores the plugin token in `chrome.storage.local` and exercises the API.
  - `background.mjs` — service worker stub.
  - `icon.svg` — simple extension icon.
  - `test-node.mjs` — Node runner that round-trips the client against a Core instance for all three providers.
  - `README` — install and security notes (plain text to avoid new `.md` files).
- `mock_core/main.py` — added `browser_extension` packaging and downloads to the example plugin manifest.
- `tests/conftest.py` — added a session-scoped `live_mock_server` fixture for tests that need a real HTTP socket.
- `tests/test_browser_extension.py` — Python test that validates `manifest.json` and runs `test-node.mjs` against a live `mock_core`.
- `BLUEPRINT.md` — no change in this session.

### Verification

- `python -m py_compile tests/conftest.py tests/test_browser_extension.py tests/test_local_script.py mock_core/main.py`: PASS
- `pytest tests/ -v`: **15 passed** (8 local_script tests + 2 browser_extension tests + 5 parametrized provider tests)
- Manual Node round-trip against `uvicorn mock_core.main:app --port 9000`:
  - list, get, connect, me, download for Google Drive/Dropbox/OneDrive, upload for all three, complete — all OK.
- Pushed to `1semptify-arch/Semptify-PI` at `2aaae69`.

### Notes

- The popup UI was not loaded in a real browser in this commit. The JS client logic is the primary surface; full browser extension load verification is deferred to a later phase with appropriate tooling.
- No business-model language in any user-facing copy. The extension uses "Connect" and "Plugin token," not "log in" or "sign up."

---

## Session — 2026-09-01 — Record Semptify-PI roadmap and begin Phase 1

### Task

- **Task ID:** `septify-pi-roadmap-2026-09-01`
- **Scope:** Phase 0: update `BLUEPRINT.md` and `BUILD_STATE.md` with current status and the Roadmap to Live on Render. Phase 1: build the `browser_extension` reference plugin.

### What changed

- `BLUEPRINT.md` — rewritten to reflect current status and the phased roadmap. Explicitly scoped to Semptify-PI only; Core Preamble and public `semptify.org` pages are out of scope.
- `BUILD_STATE.md` — this entry.

### Roadmap summary

| Phase | Work | Sign-off needed |
|-------|------|-----------------|
| 0 | Record roadmap and status | No |
| 1 | `browser_extension` reference plugin | No |
| 2 | Real Core OAuth/token implementation | Yes (before start and before close) |
| 3 | Provider OAuth app registration (Brad-only) | N/A — Brad action |
| 4 | Public plugin directory / explainer | Yes (final copy) |
| 5 | Render deployment | No |
| 6 | Go-live verification | Yes (final go/no-go) |

### Verification

- `BLUEPRINT.md` is scoped to PI and references the confirmed provider-differentiated contract.
- `BUILD_STATE.md` reflects the roadmap and the start of Phase 1.

---

# Semptify-PI Build State

## Session — 2026-09-01 — Confirm Dropbox and OneDrive direct-capability shapes

### Task

- **Task ID:** `septify-pi-provider-direct-url-2026-09-01` (continued)
- **Scope:** Answer the two follow-up questions in the hand-off: confirm Dropbox/OneDrive behavior and prove the contract is provider-differentiated, not Google-Drive-only.

### What changed

- `docs/design-spec.md` — rewrote section 6 "Zero-transfer document access" with provider-specific read/write tables and the dual-shape client rule.
- `mock_core/main.py` — added a test-only `provider` query parameter to `download-url` and `upload-url` (default `google_drive`, hidden from OpenAPI) and implemented `dropbox` and `onedrive` response shapes alongside the existing `google_drive` direct_request.
- `tests/test_local_script.py` — added `pytest.mark.parametrize` to `test_download_url_by_provider` and `test_upload_url_by_provider`, covering all three providers.

### Answers to the hand-off questions

1. **Dropbox and OneDrive confirmed.**
   - **Dropbox download:** `files/get_temporary_link` returns a preauthenticated tokenless URL.
   - **Dropbox upload:** `files/upload` requires `Authorization: Bearer <token>` and a `Dropbox-API-Arg` header — no tokenless upload URL.
   - **OneDrive download:** `@microsoft.graph.downloadUrl` is a preauthenticated tokenless URL.
   - **OneDrive upload:** `createUploadSession` returns a preauthenticated `uploadUrl` the client PUTs bytes to.

2. **The contract is provider-differentiated, not Google-Drive-only.**
   - `download-url` and `upload-url` each return either a preauthenticated bare URL (`download_url`/`upload_url`) **or** a `direct_request` describing the HTTP call the plugin must make itself.
   - Client rule: prefer `direct_request` if present; otherwise use the bare URL.

### Provider response matrix

| Provider | Read shape | Write shape |
|----------|------------|-------------|
| Google Drive | `direct_request` (GET `files.get?alt=media` with `Authorization`) | `direct_request` (POST resumable session with `Authorization`) |
| Dropbox | `download_url` (tokenless temporary link) | `direct_request` (POST `files/upload` with `Authorization` + `Dropbox-API-Arg`) |
| OneDrive | `download_url` (tokenless `@microsoft.graph.downloadUrl`) | `upload_url` (tokenless resumable `uploadUrl`) |

### Verification

- `python -m py_compile mock_core/main.py tests/test_local_script.py`: PASS
- `pytest tests/ -v`: **13 passed**
- Manual CLI round-trip against `uvicorn mock_core.main:app --port 9000` with default `google_drive`: connect, download-url, upload-url, complete-upload all OK.

---

## Session — 2026-09-01 — Correct direct-capability contract for Google Drive

### Task

- **Task ID:** `septify-pi-provider-direct-url-2026-09-01`
- **Scope:** Validate how Google Drive, Dropbox, and OneDrive expose direct file access; update the Semptify-PI spec and `mock_core` so the contract matches reality.

### What changed

- `plugin_api_spec/openapi.yaml` — added `DirectRequest` schema, made `download_url`/`upload_url` optional, added `direct_request` to `DirectUrlResponse` and `UploadUrlResponse`, and updated examples/descriptions for Google Drive, Dropbox, and OneDrive.
- `docs/design-spec.md` — moved "provider-specific direct URL support" from open questions to resolved with the dual-shape contract.
- `mock_core/main.py` — added `DirectRequest` Pydantic model, made response models optional, changed `download-url` and `upload-url` to simulate Google Drive by default (per-request `Authorization` bearer token, resumable upload session creation).
- `tests/test_local_script.py` — updated `test_download_url` and `test_upload_url_and_complete` to assert the new `direct_request` shape.
- `BUILD_GUIDE.md` — no change.

### Findings

- **Google Drive**: No tokenless direct URL. Every `files.get?alt=media` call and resumable upload session creation requires a scoped provider bearer token. Core can broker the token; the plugin makes the request directly; bytes never touch Core.
- **Dropbox**: `files/get_temporary_link` returns a preauthenticated tokenless download URL valid ~4h. Uploads require a bearer token on every request.
- **OneDrive**: `@microsoft.graph.downloadUrl` is a preauthenticated tokenless download URL. `createUploadSession` returns a preauthenticated `uploadUrl` the client `PUT`s bytes to.

### Contract rule

- `download-url` / `upload-url` responses now return either a preauthenticated bare URL **or** a `direct_request` object with `endpoint`, `method`, `headers`, optional `query`, and optional `body`.
- Client rule: prefer `direct_request` when present; otherwise fall back to `download_url` / `upload_url`.

### Verification

- `python -m py_compile mock_core/main.py local_script/*.py tests/*.py`: PASS
- `pytest tests/ -q`: 8 passed
- Manual CLI round-trip against `uvicorn mock_core.main:app --port 9000`:
  - `connect example-document-organizer`: OK
  - `download-url doc_123`: returns Google Drive-style `direct_request` with `Authorization` header
  - `upload-url notice.pdf --parent-folder /Semptify5.0/Inbox`: returns resumable session `direct_request`
  - `complete <completion_token> provider_abc notice.pdf --size 1024`: OK

---

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
