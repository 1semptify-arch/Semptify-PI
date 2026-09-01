# Semptify-PI Build Blueprint

**Repo root:** `C:\master-repo\sources\app-semptify-pi`  
**Last updated:** 2026-09-01  
**Status:** Phase 0 complete; Phase 1 in progress

This blueprint is scoped to **Semptify-PI only**. The Semptify Core Preamble
(onboarding, vault, document center) and the public `semptify.org` site are
managed in `C:\master-repo\modules\app-semptify-fastapi` and are not in scope
here. The Core-wide "module blueprint / narrative interpreter" initiative is a
separate, later effort.

---

## 1. What Semptify-PI is

Semptify-PI is the **Semptify Plugin Interface**: the public API, manifest
format, and reference client plugins that let tenant-side tools read from and
write to a tenant's own cloud storage without Semptify Core ever handling
document bytes.

Current components:

- `plugin_api_spec/` — OpenAPI spec and manifest JSON schema.
- `mock_core/` — standalone FastAPI test double for the plugin API.
- `local_script/` — first reference plugin (Python CLI).
- `browser_extension/` — next reference plugin (Phase 1).
- `desktop_app/` — later reference plugin (after Phase 1, before real Core).
- `docs/design-spec.md` — architecture and contract decisions.

---

## 2. Current status

- **Provider direct-capability contract confirmed** for Google Drive, Dropbox,
  and OneDrive. The API returns either a preauthenticated bare URL or a
  `direct_request` describing an HTTP call the plugin must make itself.
- **`local_script` reference plugin** round-trips cleanly against `mock_core`
  for all three provider shapes.
- **`docs/design-spec.md`** and **`plugin_api_spec/openapi.yaml`** updated to
  reflect the dual-shape contract.
- **`BUILD_STATE.md`** logs the work to date.

---

## 3. Roadmap to live on Render

Phases marked with **🛑** require Brad sign-off. All other phases are scoped
for the agent to complete, verify, commit, and request push approval.

### Phase 0 — Reconcile scope (done)

- [x] Confirm PI `BLUEPRINT.md` is scoped to PI only.
- [x] Update `BLUEPRINT.md` and `BUILD_STATE.md` with current status and this
      roadmap.

### Phase 1 — `browser_extension` reference plugin (done)

- [x] `browser_extension/` package with Manifest V3, popup, shared `api-client.mjs`,
      and Node test runner.
- [x] `tests/test_browser_extension.py` with live `mock_core` fixture.
- [x] Verification: `py_compile`, `pytest tests/ -q` (15 passed), manual Node
      round-trip across Google Drive/Dropbox/OneDrive.

### Phase 2 — Real Core implementation (next)

**No sign-off needed.** This is the second reference plugin. It follows the
same pattern as `local_script` and proves the provider-differentiated contract
in a browser context.

- Implement `browser_extension/` package:
  - Config loading (browser storage or content script context).
  - Client that calls the Semptify-PI endpoints.
  - Minimal entry point/background script that demonstrates list, connect,
    me, download-url, upload-url, and complete-upload.
- Add tests under `tests/` that exercise it against `mock_core` for all three
  provider shapes.
- Verification: `python -m py_compile`, `pytest tests/ -q`, manual round-trip
  against `mock_core`.

### Phase 2 — Real Core implementation

**🛑 Sign-off checkpoint: before starting.** Security-critical — real OAuth,
real token issuance, real tenant cloud access.

- Design and implement real OAuth flows for Google Drive, Dropbox, and OneDrive
  using the confirmed per-provider contract shapes.
- Real scoped token issuance, expiry, and revocation.
- Real plugin manifest registry (minimal, supporting only `local_script` and
  the Phase 1 plugin).
- Prove the "Core never sees bytes" property against real provider APIs.

**🛑 Sign-off checkpoint: before Phase 2 is marked done.** Security/privacy
review of the real OAuth/token implementation.

### Phase 3 — Provider credentials (Brad-only)

- Brad personally registers OAuth apps with Google Cloud Console, Dropbox App
  Console, and Microsoft Entra/Azure.
- Agent wires credentials into Render environment variables — never committed
  to the repo.

### Phase 4 — Public plugin directory / capability explainer

- Build directory page(s) on the PI/Render host:
  - What plugins are.
  - How to use `local_script` and the Phase 1 plugin.
  - API spec link for third-party developers.
- Content follows canonical language rules (plain, crisis-appropriate,
  no paid tiers, no dark patterns).

**🛑 Sign-off checkpoint: final copy review before publishing.**

### Phase 5 — Render deployment

- Provision a new Render service for the real Core.
- Provision production Postgres on Render (separate from local
  `semptify_pi`).
- Wire Phase 3 credentials as Render env vars.
- Deploy and run smoke tests against the live Render URL.

### Phase 6 — Go-live verification

**🛑 Sign-off checkpoint: final go/no-go.**

- Full test suite + guardrail checks pass against the deployed instance.
- Security/privacy review confirms zero-transfer holds in production.
- Brad's explicit go-ahead to open it publicly.

---

## 4. Source-of-truth documents

| Artifact | Purpose | Status |
|---|---|---|
| `BLUEPRINT.md` | This build plan. | **Current.** |
| `BUILD_STATE.md` | What shipped, what is broken, what is pending. | **Current.** |
| `AGENTS.md` | Agent rules, Python 3.11.9 mandate, known failure registry. | **Exists.** |
| `docs/design-spec.md` | Architecture and contract decisions. | **Current.** |
| `plugin_api_spec/openapi.yaml` | Public plugin API spec. | **Current.** |
| `plugin_api_spec/manifest.schema.json` | Plugin manifest schema. | **Current.** |
| `BUILD_GUIDE.md` | How to build, run, test. | **Exists; update as tooling changes.** |

Other canonical Core documents (`PROJECT_BIBLE.md`, `DEPLOYMENT_READINESS.md`,
`SECURITY_AND_PRIVACY_ARCHITECTURE.md`, `docs/DICTIONARY.md`, `docs/adr/`)
belong in the Semptify Core repo unless they describe PI-specific concerns.

---

## 5. Naming and commit conventions

1. **Packages:** `mock_core/`, `local_script/`, `browser_extension/`, `desktop_app/`.
2. **Branches:** `feature/pi-<module>-<desc>`, `fix/pi-<issue>`, `reconciliation/pi-<date>`.
3. **Tasks:** `pi-<module>-<short-desc>-YYYY-MM-DD`.
4. **Commits:** `<category>: <imperative>` where category is `admin:`, `user:`, `help:`, `adr:`.
5. **One task per commit.**
