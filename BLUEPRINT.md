# Semptify-PI Build Blueprint

**Repo root:** `C:\master-repo\sources\app-semptify-pi`  
**Date:** 2026-08-30  
**Status:** Planning — no implementation code yet  

This blueprint is the single source of truth for what must exist before construction begins. It reflects Brad's direction that the immediate work is the **Preamble** (core Semptify onboarding, vault, and document center) and a public `Semptify.org` web presence, with offline and agency features deferred 1–3 months.

---

## 1. What the "Preamble" is

The Preamble is the first experience every user — tenant, advocate, developer, admin — must be able to complete:

1. **Onboarding** — connect storage (OAuth), create vault folders, land in the tenant home.
2. **Vault** — upload, list, retrieve documents/photos from the tenant's own cloud storage.
3. **Document Center** — view, organize, and take next steps on uploaded records.

Without the Preamble working, every other feature (plugins, offline, agency) has no foundation.

**Where it lives:** This functionality is in the Semptify Core repo (`C:\master-repo\modules\app-semptify-fastapi`), because that is the canonical tenant-facing service. Semptify-PI stays decoupled and uses only the public plugin API surface.

---

## 2. Public web presence — `Semptify.org`

Brad's requirement: a real web presence with enough information and working entry points.

### Pages/portals required

| Path | Purpose | Notes |
|---|---|---|
| `/` | Public landing | Already exists as `index.html`. Needs expanded copy and CTAs. |
| `/law-library` or `/renters-guide` | Public rights information | Currently redirects to `/law-library`. Needs content. |
| `/help` | Help, hotlines, resources | Already referenced; needs content and routing. |
| `/developers` | Developer/plugin portal | Explains `Semptify-PI` and the plugin API. |
| `/admin` | Admin/mission-control portal | Role-gated; links to admin tools. |
| `/plugins` (or `plugins.semptify.org`) | Plugin directory | Links to browser extension, desktop app, local script downloads. |

### Promise / blocker analysis

- **No "log in / sign in / account" language** — all CTAs use "connect your storage" or "link your Drive."
- **No paid tiers** — plugin directory is public-service only.
- **No tenant-facing legal conclusions** — law library states rights and next steps, not outcomes.
- **No PII on public pages** — no names, addresses, case numbers.
- **No dark patterns** — no urgency, fear, or deceptive framing.

### Semptify-PI connection

The `Semptify-PI` plugin directory is a natural part of the public site. The current design spec has two open decisions:

1. Plugin directory location: `semptify.org/plugins` vs. `plugins.semptify.org`.
2. Build order: ship one reference plugin first, or publish the API spec first.

This blueprint recommends `semptify.org/plugins` as a path under the main public site (simpler trust/cookies) and shipping the API spec + `mock_core` before a reference plugin.

---

## 3. Build-system prerequisites

Before any construction, the following artifacts must exist in **both** the Semptify Core repo and the Semptify-PI repo (where applicable).

### 3A. Source-of-truth documents

| Artifact | Purpose | In Semptify-PI? |
|---|---|---|
| `BLUEPRINT.md` | The single product/build plan. | **Yes** (this file) |
| `PROJECT_BIBLE.md` | Doc hierarchy, identity, governance. | **Yes** — to be created |
| `AGENTS.md` | Agent rules, known failure registry, Python mandate. | **Yes** — exists, expand |
| `BUILD_STATE.md` | What shipped, what is broken, what is pending. | **Yes** — to be created |
| `ACTIVE_CONTEXT.md` | What is being worked on right now. | **Yes** — to be created |
| `BUILD_GUIDE.md` | How to build, run, test, deploy. | **Yes** — to be created |
| `SECURITY_AND_PRIVACY_ARCHITECTURE.md` | Data flow, token scope, PII boundaries. | **Yes** — to be created |
| `DEPLOYMENT_READINESS.md` | Production checklist. | **Yes** — to be created |
| `docs/DICTIONARY.md` | Canonical terms (no "evidence/proof" before court, no "log in"). | **Yes** — to be created |
| `docs/adr/` | Architecture Decision Records. | **Yes** — to be created |
| `apps.yaml` (already exists) | Source of truth for which services run. | **Yes** |

### 3B. Tooling and automation

1. Python 3.11.9 virtual environment and locked `pyproject.toml` (already pins 3.11.9).
2. `pytest` suite and `tests/` directory.
3. `python -m py_compile <file>` compile check.
4. CI workflow (`.github/workflows/ci.yml`).
5. Pre-commit hooks for compile and test.
6. `tools/orchestrator_state.json` at the master-repo level (already exists) extended to track Semptify-PI tasks.
7. `tools/orchestrator_mark_task.py` and `tools/handoff_template.md` used for PI work.
8. Branch protection and naming rules.

### 3C. Naming rules

1. **Modules/packages:** `mock_core/`, `local_script/`, `desktop_app/`, `browser_extension/` (no `v2`/`new`).
2. **Branches:** `feature/pi-<module>-<desc>`, `fix/pi-<issue>`, `reconciliation/pi-<date>`, `adr/pi-<decision>`.
3. **Tasks:** `pi-<module>-<short-desc>-YYYY-MM-DD`.
4. **Commits:** `<category>: <imperative>` where category is `admin:`, `user:`, `help:`, `adr:`.
5. **Handoffs:** `handoffs/<task-id>-YYYY-MM-DD.md`.

### 3D. Orchestrator improvements needed

1. Task dependency graph (Preamble must come before plugin directory).
2. Cross-repo task tracking (Core vs. PI both in `orchestrator_state.json`).
3. Verification capture on every resolved task (compile/test).
4. Known-failure early warning.
5. STOP trigger for anything touching `app/modules/onboarding/` in Core (NO-TOUCH).
6. One-task-per-commit enforcement.

---

## 4. Immediate build sequence

### Phase 0 — Factory setup (do not skip)
1. Create `PROJECT_BIBLE.md`, `BUILD_STATE.md`, `ACTIVE_CONTEXT.md`, `BUILD_GUIDE.md`, `SECURITY_AND_PRIVACY_ARCHITECTURE.md`, `DEPLOYMENT_READINESS.md`, `docs/DICTIONARY.md`, and `docs/adr/` in `app-semptify-pi`.
2. Add Semptify-PI tasks to the master `orchestrator_state.json`.
3. Set up CI and pre-commit for `app-semptify-pi`.
4. Update `apps.yaml` with explicit `status`, `test_command`, and `deploy_target` for each service.

### Phase 1 — Preamble (Semptify Core)
1. Verify onboarding, vault, and document center are end-to-end in Core.
2. Resolve any remaining UI/flow gaps.
3. Add/update BUILD_STATE entries for each.

### Phase 2 — Public website / `Semptify.org`
1. Expand `index.html` landing page.
2. Add `/help`, `/developers`, `/admin`, and `/plugins` pages/routes.
3. Wire law library and plugin directory to the same navigation registry (SSOT).
4. Verify with real browser interactions (IronBee DevTools).

### Phase 3 — Semptify-PI reference implementation
1. Finalize `plugin_api_spec/` OpenAPI + JSON Schema.
2. Land `mock_core` test double.
3. Publish plugin API docs on `/developers`.
4. Land one reference plugin (`local_script` or `browser_extension`).

### Phase 4 — Offline and agency (1–3 months out)
1. Write ADRs for offline cache and agency consent/context model.
2. Get Brad sign-off.
3. Build incrementally, one task per commit.

---

## 5. Decisions captured

| # | Question | Decision |
|---|---|---|
| 1 | Public site location | `Semptify.org` is served from Semptify Core (`modules/app-semptify-fastapi`). This is the canonical tenant-facing service and already owns `/`, law library, and admin/tenant portals. |
| 2 | Plugin directory | Render separate instance. The exact domain is TBD; use an environment variable (`SEPTIFY_PI_DIRECTORY_URL`) so it can be set without code changes. Candidate: `plugins.semptify.org` or a Render subdomain (e.g., `semptify-plugins.onrender.com`). |
| 3 | Preamble first | **Yes.** Verify Core Preamble (onboarding, vault, document center) before any other work. No exceptions. |
| 4 | PI build-system docs | Brad leaves this to the orchestrator. Create a lightweight PI build-system scaffold now so the factory exists, then move to Core Preamble. |

### Still open

- **Plugin directory domain:** Decide once the Render instance is created.
- **Agency/offline priority:** Deferred 1–3 months.

---

## 6. Notes on current state

- Semptify-PI currently has the initial scaffold: `mock_core/`, `local_script/`, `desktop_app/`, `browser_extension/`, `plugin_api_spec/`, `docs/design-spec.md`, `apps.yaml`, `pyproject.toml`.
- No app code is committed yet.
- The design spec already defines the zero-transfer client-side plugin architecture and the `plugin_tokens` model.
- Semptify Core has an existing public landing page (`/`), law library, and admin/tenant portals. These can be expanded for `Semptify.org`.
