# Design Spec: Zero-Transfer Client-Side Plugin Architecture

**Task:** `plugin-arch-design-spec-2026-08-28`  
**Date:** 2026-08-29  
**Agent:** Claude  
**Status:** Design spec — planning only, no implementation code  

**Sources read for this spec:**
- `C:\master-repo\modules\app-semptify-fastapi\tools\agent_orchestrator_tasks.json` (task `plugin-arch-design-spec-2026-08-28`)
- `C:\master-repo\handoffs\plugin-architecture-tasklist-2026-08-28.md` (the locked decisions this spec must follow)
- `C:\master-repo\handoffs\plugin-architecture-clientside-research-2026-08-28-report.md` (the research this builds on)
- `C:\master-repo\modules\app-semptify-fastapi\app\core\security.py` (current auth, session, and function-token patterns)
- `C:\master-repo\modules\app-semptify-fastapi\app\core\user_context.py` (`UserContext`, `StoredSession`, permissions)
- `C:\master-repo\modules\app-semptify-fastapi\app\core\cookie_auth.py` (HMAC-signed `semptify_uid` cookie)
- `C:\master-repo\modules\app-semptify-fastapi\app\modules\storage\router.py` (provider token storage and refresh)
- `C:\master-repo\modules\app-semptify-fastapi\app\core\features.py` (feature-flag conventions)

---

## 1. What this spec is and is not

This is a **planning document**. It does not commit any code. It defines a client-side plugin architecture for Semptify that follows the locked decisions from `plugin-architecture-tasklist-2026-08-28.md`:

1. **Packaging:** plan for all three candidates — D (browser extension), E (desktop app), F (local script). No priority order.
2. **Token scope:** scoped, per-endpoint tokens only. A plugin token must never grant full tenant access.
3. **Document access — zero-transfer model:** Semptify Core never touches document bytes, even as a mediator. The plugin runs on the user's own machine and connects directly to the tenant's cloud storage (Google Drive, Dropbox, OneDrive) using the same storage-as-identity OAuth grant that already exists. Core's role is identity/permission confirmation only.

The earlier research report (`plugin-architecture-clientside-research-2026-08-28-report.md`) is superseded on one key point: it recommended that **Core mediate all storage access** ("plugin asks Core for a file, Core reads it and returns the result"). The later-locked decision is stricter: **Core must not transport document bytes at all**. This spec replaces the "through Core" flow with a **capability/direct-URL flow**.

### Decisions resolved

- **Plugin directory location:** both pieces exist, at different times and domains.
  - `semptify.org/plugins` is the in-Core landing/explainer page (already approved for Core; see `add-plugins-landing-page-2026-08-30`).
  - `plugins.semptify.org` (or wherever the Render-deployed directory is hosted) becomes the real plugin directory and the redirect destination once it is live.
- **Build order:** ship a reference plugin first (`local_script` is the smallest), then publish the spec. The spec stays provisional until a real client has round-tripped against it.

---

## 2. Core architecture at a glance

```
Tenant's machine
================
+-----------------+
| Plugin (D/E/F)  |
| - local compute |
| - bearer token  |
| - local storage |
+--------+--------+
         |
         | Authorization: Bearer <plugin_token>
         |
         v
+-----------------------------+
| Semptify Core               |
| (Python 3.11.9, FastAPI)    |
|                             |
| /api/v1/plugins/*           |  <- directory, connect, revoke
| /api/v1/plugin/capability/* |  <- returns direct provider URLs
| /api/v1/* (other endpoints) |  <- scoped to token permissions
| token validation            |
| rate limiting               |
| CORS (for D)                |
+-----------------------------+
         |
         | identity/permission confirmation only
         | (Core may call provider to create short-lived direct URLs
         |  but never streams or stores document bytes)
         v
+-----------------+
| Tenant's cloud  |
| (Drive/Dropbox/ |
|  OneDrive)      |
+-----------------+
```

---

## 3. Token issuance flow

### 3.1 Why a new token is needed

Semptify's current browser session uses two mechanisms:

- `semptify_uid` cookie: HMAC-signed `user_id` (`app/core/cookie_auth.py`).
- `semptify_session` cookie or `Authorization: Bearer <session_id>` header: maps to a `StoredSession` in Redis or memory (`app/core/security.py`, `app/core/user_context.py`).

A client-side plugin cannot use either:
- It is not on the `semptify.org` origin, so it cannot read cookies.
- Even if it could, the `semptify_uid` signature is tied to `SECRET_KEY`, which the plugin must never hold.
- Session IDs are short-lived browser-session keys tied to web flows, not to a persistent remote client.

`app/core/security.py` already has `issue_function_access_token()`, but it is intentionally short-lived (5 minutes) and stored in memory. That pattern is useful for overlay/function access, not for long-lived plugin tokens.

### 3.2 Plugin token model (proposed)

A persistent `plugin_tokens` table (or equivalent). It stores the token hash, not the raw token, because the raw token is shown only once when issued.

| Field | Purpose |
|-------|---------|
| `token_hash` (PK) | SHA-256 of the raw bearer token. The only stored identifier. |
| `user_id` | The tenant's `semptify_uid` (e.g., `GT7x9kM2pQ`). |
| `plugin_id` | Which plugin this token is for. |
| `scopes` | List of permitted endpoint/permission identifiers. |
| `packaging` | `browser_extension`, `desktop_app`, or `local_script`. |
| `created_at` | Token creation time. |
| `expires_at` | Optional token expiry. |
| `last_used_at` | Last successful use. |
| `revoked` | Boolean. |
| `revoked_at` | If revoked. |
| `label` | Optional user-provided name (e.g., "Firefox extension"). |

The token itself is a long random string, e.g. `secrets.token_urlsafe(32)`. A prefix such as `pl_` can make plugin tokens visually distinct from session IDs and simplify routing.

### 3.3 Issuance steps

1. Tenant is already connected to Semptify in their browser (has a valid `semptify_uid` / `semptify_session`).
2. Tenant visits the plugin directory and selects a plugin.
3. Tenant clicks **Connect this plugin**.
4. Core validates:
   - The user's session is active.
   - The `plugin_id` exists and is approved.
   - The requested `packaging` is one of the plugin's declared packaging types.
   - Every scope in the plugin manifest is allowed for the user's role (intersection with `UserContext` role permissions).
5. Core generates the raw token, stores a hash, and returns the raw token to the tenant exactly once.
6. The tenant copies the token into the plugin's config, or a redirect/pairing flow delivers it automatically.
7. The plugin stores the token in its own local storage:
   - **D (browser extension):** `browser.storage.local` (extensions cannot use cookies for cross-origin requests).
   - **E (desktop app):** OS keychain (Windows Credential Manager, macOS Keychain, Linux secret service).
   - **F (local script):** `config.json` or environment variable.
8. On every API call, the plugin sends `Authorization: Bearer <plugin_token>`.

### 3.4 Validation and per-endpoint scoping

A new `get_current_plugin_user()` auth dependency is proposed. It would:

1. Read `Authorization: Bearer <plugin_token>`.
2. Look up the token hash in `plugin_tokens`.
3. Verify the token is not expired or revoked.
4. Load the user's role and storage provider from the existing `User` / `Session` tables.
5. Build a `UserContext` whose **effective permissions are the intersection of**:
   - the plugin token's `scopes`, and
   - the user's role permissions (`app/core/user_context.py` `ROLE_PERMISSIONS`).
6. If the requested endpoint is not covered by the resulting permissions, return `403 Forbidden`.

This enforces the "per-endpoint" and "never full tenant access" rules. A plugin token cannot do anything the tenant user themselves cannot do, and it is further restricted to the endpoints listed in its manifest.

### 3.5 Scope naming

Scopes are endpoint-oriented. They map cleanly to the existing `FunctionGroupContract` and permission system. Example conventions:

```
vault:read
timeline:read
timeline:write
law_library:read
resources:read
context:read
context:write
documents:capability   # needed to request direct provider URLs for document read/write
```

A plugin manifest declares `required_scopes`. During the connect flow, Core checks those against the user's role. The issued token carries the exact approved list.

### 3.6 Revocation

- Tenant can view and revoke plugin tokens from a **Connected plugins** page.
- Revocation deletes the row (or sets `revoked=true`) immediately.
- Next plugin request with that token gets `401 Unauthorized`.
- On user disconnect or role change, Core can call `invalidate all plugin tokens for user_id`.

---

## 4. Plugin manifest format

A plugin must declare what it is, what it can do, and how to install it. The manifest is stored in Core's plugin directory and is the source of truth for the connect flow.

### 4.1 Proposed manifest schema

```json
{
  "plugin_id": "example-document-organizer",
  "name": "Document Organizer",
  "version": "1.0.0",
  "description": "Sorts and labels documents in your Semptify vault.",
  "author": "Semptify or trusted contributor",
  "license": "AGPL-3.0",
  "homepage_url": "https://semptify.org/plugins/example-document-organizer",
  "privacy_policy_url": "https://...",
  "support_url": "https://...",
  "packaging": ["browser_extension", "desktop_app", "local_script"],
  "required_scopes": ["vault:read", "vault:write", "documents:capability"],
  "optional_scopes": ["context:read"],
  "api_version": "v1",
  "downloads": {
    "browser_extension": {
      "chrome_web_store_url": "...",
      "firefox_addon_url": "...",
      "sideload_url": "..."
    },
    "desktop_app": {
      "windows": "...",
      "macos": "...",
      "linux": "..."
    },
    "local_script": {
      "python": "...",
      "node": "..."
    }
  },
  "connect": {
    "browser_extension_origin": "chrome-extension://<id>",
    "desktop_redirect_scheme": "semptify-plugin://",
    "local_script_config_template": "..."
  },
  "icon_url": "...",
  "status": "approved"
}
```

### 4.2 Important fields

- `plugin_id` is the unique slug. It appears in directory URLs, token rows, and plugin headers.
- `packaging` controls which install types Core offers for this plugin.
- `required_scopes` are the minimum scopes the plugin needs. They cannot include any administrative or user-management scopes.
- `optional_scopes` can be requested per install and are subject to the same role intersection.
- `connect.browser_extension_origin` is used for CORS and `postMessage` validation.
- `connect.desktop_redirect_scheme` is used to return a token to a desktop app after browser pairing.

---

## 5. How each candidate authenticates

### 5.1 D — Browser extension

**Install:** Chrome Web Store, Firefox Add-ons, or sideloaded `.crx` / `.xpi`.

**Auth flow:**
1. Extension opens a small popup or sidebar with a **Connect to Semptify** button.
2. Button opens a browser tab to `https://plugins.semptify.org/plugins/connect?plugin_id=...` (or the equivalent Render-hosted domain).
3. The tenant is already logged into Semptify in that browser, so the connect page sees the active session.
4. After the tenant clicks **Allow**, Core issues a plugin token and either:
   - displays the token for the user to copy and paste into the extension, or
   - in a later iteration, uses `postMessage` back to the extension's origin (declared in the manifest) to deliver it.
5. The extension stores the token in `browser.storage.local`.
6. The extension's background script or content script injects `Authorization: Bearer <token>` on `fetch()` calls to `https://<domain>/api/v1/*`.

**CORS:** Core must include `Access-Control-Allow-Origin` for the manifest-declared `browser_extension_origin`. Credentials should not be sent cross-origin; the bearer header is sufficient.

**Compute limitations:** The extension is limited to browser APIs. It cannot run local LLMs or OCR directly, but it can call Core for structured data and use direct provider URLs for document access.

### 5.2 E — Desktop app

**Install:** Download `.exe` / `.dmg` / `.AppImage` from the plugin directory.

**Auth flow (recommended): pairing-code or custom-scheme redirect**

**Pairing-code option (simpler and safer for first pass):**
1. App shows a screen with a **Get token from Semptify** button.
2. Button opens the system browser to `https://<domain>/plugins/connect?plugin_id=...&mode=desktop`.
3. Tenant clicks **Allow**; Core displays a short, one-time pairing code.
4. Tenant enters the code in the app.
5. App exchanges the code for the token via `POST /api/v1/plugins/pair`.
6. App stores the token in the OS keychain.

**Custom-scheme redirect option (smoother, later):**
1. App opens browser to `https://<domain>/plugins/connect?plugin_id=...&return=semptify-plugin%3A%2F%2Fcallback`.
2. After allow, Core redirects to `semptify-plugin://callback?token=...`.
3. App intercepts the custom scheme, extracts the token, and stores it.

**Storage:** Token in OS keychain. Refresh token (if we add one) also in keychain.

**Compute:** Full local file system, local AI, OCR, PDF tools. Best fit for heavy document processing.

### 5.3 F — Local script

**Install:** Download a `.py` or `.js` file and a `plugin-config.json` template.

**Auth flow:**
1. Script package includes `config.json` with a placeholder token.
2. Tenant opens `https://<domain>/plugins/connect?plugin_id=...&mode=script`.
3. Tenant clicks **Allow**; Core shows the token.
4. Tenant copies the token into `plugin-config.json`.
5. Script reads `config.json` and sends the token on every HTTP call.

**Storage:** Token in the local config file or environment variable. Tenant is responsible for file permissions.

**Compute:** Whatever the local Python/Node runtime can do. Intended for developers, advocates, and power users — not a tenant in crisis.

---

## 6. Zero-transfer document access

This is the most important change from the earlier research report. Core does **not** read document bytes and pass them to the plugin. Core acts as a permission authority and returns either a short-lived, preauthenticated direct URL or a `direct_request` the plugin uses to call the provider itself. In both cases, bytes move only between the plugin and the tenant's cloud provider.

### 6.1 Read flow

```
Plugin                          Core                       Provider
  |                              |                            |
  | POST /api/v1/plugin/files/{file_id}/download-url          |
  | Authorization: Bearer <plugin_token>                      |
  |----------------------------->|                            |
  |                              | 1. Validate plugin token     |
  |                              | 2. Check scope "vault:read"  |
  |                              | 3. Load tenant's encrypted   |
  |                              |    OAuth token from sessions |
  |                              | 4. Ask provider for a direct |
  |                              |    capability (URL or request|
  |<-----------------------------| return {download_url} or     |
  |    download_url / direct_req |     {direct_request}         |
  |                              |                            |
  | GET <download_url>  OR       |                            |
  | GET/POST as directed         |                            |
  |----------------------------------------------------------->|
  | (document bytes flow directly between provider and plugin) |
```

### 6.2 Provider-specific read behavior

| Provider | Core can obtain a preauthenticated, tokenless URL? | What the plugin receives |
|----------|---------------------------------------------------|--------------------------|
| **Dropbox** | Yes — `files/get_temporary_link` returns a direct link valid ~4 hours. | `download_url` |
| **OneDrive** | Yes — `GET /drive/items/{id}?select=@microsoft.graph.downloadUrl` returns a preauthenticated URL. | `download_url` |
| **Google Drive** | No — binary content requires `files.get?alt=media` with a bearer token on every request. | `direct_request` with `Authorization: Bearer <scoped_provider_token>` and `alt=media` query. |

### 6.3 Write flow

The same zero-transfer principle applies, but the response shape varies by provider:

1. Plugin requests `POST /api/v1/plugin/files/upload-url` with a proposed filename and parent folder.
2. Core validates the plugin token and `vault:write` scope.
3. Core asks the provider for an upload capability and returns:
   - an `upload_url` if the provider gives a preauthenticated URL the plugin can PUT/POST to directly, **or**
   - a `direct_request` describing the HTTP request the plugin must make to start the upload (for example, Google Drive resumable session creation),
   - plus a `completion_token` for the plugin to report the result.
4. Plugin uploads bytes directly to the provider.
5. Plugin calls `POST /api/v1/plugin/files/complete` with the `completion_token` and provider file metadata.
6. Core records the new file in the tenant's vault index (metadata only — no bytes stored on Core).

### 6.4 Provider-specific write behavior

| Provider | Preauthenticated, tokenless upload URL? | What the plugin receives |
|----------|----------------------------------------|--------------------------|
| **Dropbox** | No — upload (`files/upload` or upload-session) requires `Authorization: Bearer <token>` on every call. | `direct_request` with endpoint, `Authorization`, and `Dropbox-API-Arg` header. |
| **OneDrive** | Yes — `createUploadSession` returns an `uploadUrl` the plugin PUTs bytes to without additional auth. | `upload_url` |
| **Google Drive** | No — resumable upload session creation requires `Authorization: Bearer <token>`; the `Location` response then gives the actual upload URL. | `direct_request` for the resumable session `POST`; the plugin follows the `Location` header. |

### 6.5 Client rule

The plugin must handle both response shapes:

- If `direct_request` is present, use it (`endpoint`, `method`, `headers`, optional `query` and `body`).
- If only `download_url` or `upload_url` is present, use that URL directly.
- Never send both shapes.

### 6.6 Key invariants

- **Document bytes never pass through Core.** Core may broker a short-lived provider token or preauthenticated URL, but it does not proxy the file content.
- **Provider tokens are scoped and short-lived.** Where Core hands a token to the plugin, it is a file- or action-scoped token, not the tenant's long-lived OAuth grant.
- **The plugin runs on the tenant's machine.** It is the only party that handles document bytes.

---

## 7. Core API surface

All plugin endpoints are under `/api/v1/` for versioning. Plugins can only reach endpoints in their token scope.

### 7.1 Plugin lifecycle endpoints

```
GET  /api/v1/plugins                    # list approved plugins (public or tenant-scoped)
GET  /api/v1/plugins/{plugin_id}        # plugin manifest
POST /api/v1/plugins/{plugin_id}/connect   # issue a plugin token (requires tenant session)
GET  /api/v1/plugins/tokens             # list the tenant's active plugin tokens
DELETE /api/v1/plugins/tokens/{token_id}   # revoke a token

POST /api/v1/plugins/pair               # exchange pairing code for token (desktop/script)
```

### 7.2 Plugin runtime endpoints

```
GET  /api/v1/plugin/me                  # current plugin context and effective scopes
POST /api/v1/plugin/files/{file_id}/download-url   # direct download URL
POST /api/v1/plugin/files/upload-url    # direct upload URL
POST /api/v1/plugin/files/complete      # notify Core of a completed direct upload
```

### 7.3 Other existing endpoints

Plugins may call existing `/api/v1/*` endpoints for structured data:

```
GET  /api/v1/documents                  # list document metadata
GET  /api/v1/timeline
POST /api/v1/timeline/events
GET  /api/v1/library/{subject}
GET  /api/v1/resources
POST /api/v1/context/query
```

Each endpoint must declare its required scope. The plugin token must include that scope, and the user must have the underlying role permission. If both are not met, the request is rejected.

### 7.4 Rate limiting

Per-token rate limits are required because a misbehaving plugin runs on the user's machine and could hammer Core. The existing `app/core/rate_limit.py` or `slowapi` pattern can be extended with a key like `plugin_token:{token_hash}`.

---

## 8. Files and modules that would change (planning only)

No edits are made now. If this spec is accepted, the likely touch points are:

- **New module:** `app/modules/plugin_gateway/` (or `app/modules/plugins/`) — router, registration, and service layer for plugin directory, connect, revoke, and capability endpoints.
- **New module:** `app/core/plugin_auth.py` — token validation and scoped `UserContext` construction.
- **New model:** `app/models/models.py` — `PluginToken` and `PluginManifest` tables.
- **Existing model:** `app/models/models.py` — `Session` (no schema change; used to retrieve the provider token for capability URL generation).
- **Existing files to reuse:**
  - `app/core/security.py` — add plugin-token validation alongside existing `get_current_user()`.
  - `app/core/user_context.py` — `UserContext` already carries role and permissions; add plugin-token scope intersection.
  - `app/modules/storage/router.py` — existing provider access and refresh logic; would be called to generate direct provider URLs.
  - `app/core/features.py` — add `Feature.PLUGIN_DIRECTORY` and `Feature.PLUGIN_API` defaulting to `False` until ready.
- **Registration:** `app/core/product_manifest.py` (later, when implementing; not now). The `SEMPTIFY_SYSTEM_MANIFEST.md` rule says new modules are registered there, never directly in `main.py`.

---

## 9. Alignment with Semptify's locked rules

| Rule | How this design stays compliant |
|------|---------------------------------|
| **Python 3.11.9 mandate** | Applies to Core only. Client-side plugins can be TS, Rust, Python, or any language that can make HTTP calls. |
| **Storage-as-identity** | Plugin tokens map to the existing `user_id`. No new identity tier. OAuth tokens stay on Core; the plugin receives only time-limited direct URLs. |
| **No PII on Semptify servers** | Client-side plugins run heavy processing on the tenant's machine. Core passes only structured metadata and short-lived URLs. Document bytes never reach Core. |
| **No "evidence"/"proof" language, no dark patterns, no paid tiers** | Plugin directory is a plain list of public-service plugins. No pricing, no gamification, no urgency tactics. |
| **No PII or case data in git** | Plugin packages are code and manifests only; tenant data lives in tenant cloud storage. |
| **One task per commit** | Build is phased: (1) Core token + directory, (2) capability URLs for read, (3) write capability, (4) first plugin. |

---

## 10. Decisions resolved and remaining open questions

The following two questions are now resolved; the rest remain open before implementation.

### Resolved

1. **Plugin directory location:**
   - `semptify.org/plugins` is the Core landing/redirect page.
   - `plugins.semptify.org` (or the Render-hosted equivalent) is the real plugin directory.

2. **Build order:**
   - Build the `local_script` reference plugin first alongside the API.
   - Publish the spec for third-party use only after the reference plugin round-trips cleanly.

### Resolved

3. **Provider-specific direct URL support:**
   - The API response for `download-url` and `upload-url` now supports two shapes, determined by the tenant's cloud provider:
     - **Preauthenticated URL:** `download_url` or `upload_url` that the plugin can fetch directly with no additional auth. Dropbox (`files/get_temporary_link`) and OneDrive (`@microsoft.graph.downloadUrl` / `createUploadSession`) can return this for download and/or upload.
     - **Direct request:** `direct_request` object with `endpoint`, `method`, `headers` (including `Authorization` when required), and optional `query`/`body`. Google Drive requires this because every `files.get?alt=media` and resumable upload session call needs a bearer token. Core can broker a scoped provider token without seeing document bytes.
   - The client rule is: **prefer `direct_request` when present; otherwise fall back to the bare URL.** This keeps `local_script` backward-compatible with tokenless providers while supporting Google Drive's per-request-token requirement.

### Remaining open

4. **Plugin manifest approval workflow:**
   - Who can approve a plugin manifest? (Admin only? Community review?)
   - Is code signing required for desktop/script plugins?

---

## 11. Recommended next step

The mock Core, OpenAPI spec, and `local_script` reference plugin now reflect the dual-shape direct-capability contract. The next task is to validate `desktop_app` and `browser_extension` packaging against the same contract, starting with whichever format exercises the Google Drive `direct_request` path most realistically. The manifest approval workflow remains a separate governance decision for later.

---

## 12. Related files and handoffs

- `C:\master-repo\handoffs\plugin-architecture-tasklist-2026-08-28.md` — the locked decisions this spec follows.
- `C:\master-repo\handoffs\plugin-architecture-clientside-research-2026-08-28-report.md` — the research report this builds on.
- `C:\master-repo\modules\app-semptify-fastapi\app\core\security.py` — existing auth and function-token patterns.
- `C:\master-repo\modules\app-semptify-fastapi\app\core\user_context.py` — `UserContext` and `StoredSession`.
- `C:\master-repo\modules\app-semptify-fastapi\app\modules\storage\router.py` — provider token storage and refresh.
