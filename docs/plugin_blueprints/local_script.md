# Plugin Blueprint: `example-document-organizer` (`local_script`)

Reference CLI plugin for the Semptify-PI `local_script` packaging.

---

## Identity / versioning

| Field | Value |
|-------|-------|
| `plugin_id` | `example-document-organizer` |
| `plugin_version` | `0.1.0` |
| `platform` | `local_script` |
| `status` | `internal-reference` |
| `name` | Document Organizer |
| `author` | Semptify |
| `license` | `AGPL-3.0` |
| `homepage_url` | `https://semptify.org/plugins/example-document-organizer` |
| `icon_url` | `https://semptify.org/static/icons/example-document-organizer.svg` |

## Narrative

### Short description

A command-line reference plugin that lists, downloads, and uploads documents in
a tenant's vault.

### Long description

The `local_script` reference plugin is a Python CLI and HTTP client that tenants
or developers can run on their own machine. It connects to the Semptify-PI Core,
obtains a scoped plugin token, then asks Core for direct provider capabilities
to move documents in and out of the tenant's own cloud storage. The plugin never
sends document bytes to Core; all storage traffic happens directly between the
plugin and the cloud provider.

## Compatibility

- **Providers:** `google_drive`, `dropbox`, `onedrive` (all three are targeted
  by the PI contract; the client passes the provider to the upload/download
  endpoints).
- **Roles:** Likely developers, technical advocates, agencies, and researchers
  who are comfortable running a local script. **Flagged for review:** whether
  non-technical tenants would use this packaging.
- **API version:** `v1`.
- **Packagings supported:** `local_script`.

## Technical contract

- **Core endpoints used:**
  - `GET /api/v1/plugins` — list approved plugins.
  - `GET /api/v1/plugins/{plugin_id}` — get plugin manifest.
  - `POST /api/v1/plugins/{plugin_id}/connect` — obtain a scoped plugin token.
  - `GET /api/v1/plugin/me` — verify plugin context.
  - `POST /api/v1/plugin/files/{file_id}/download-url` — request a download
    capability.
  - `POST /api/v1/plugin/files/upload-url` — request an upload capability.
  - `POST /api/v1/plugin/files/complete` — record a completed upload (metadata
    only).
- **Connection flow:** The CLI takes a tenant session token, calls `connect`,
  and persists the returned `plugin_token` in `local_script/config.json`.
- **Capability usage:** The client returns the full Core response. It is
  responsible for making the resulting `direct_request` or preauthenticated
  `upload_url` / `download_url` to the cloud provider. It does not interpret
  provider-specific payloads beyond passing headers and JSON bodies.
- **Containment:** The client passes `parent_folder` to `upload-url`; Core
  rejects paths that escape the configured vault folder.
- **Data the plugin sends to Core:** JSON request bodies containing file IDs,
  filenames, completion tokens, and sizes. No document bytes.
- **Zero-transfer rule:** The client code never touches a document body. It only
  carries capability URLs and metadata between Core and the provider.

## Security

- **Token storage:** The plugin token is stored in `local_script/config.json`.
  This file must be kept out of version control and should have restricted file
  permissions.
- **Secret handling:** The session token is accepted from `--session-token` or
  `SEMPIFY_PI_SESSION_TOKEN`; the plugin token is persisted locally. Provider
  capability headers (`Authorization: Bearer ...`) are used for a single request
  and are not logged.
- **Scope usage:** The client uses `vault:read`, `vault:write`, and
  `documents:capability` via the `example-document-organizer` manifest.
- **Sandbox / isolation:** The script runs in the user's local Python
  environment and has access to the local file system and network. This is the
  least sandboxed packaging.

## Tests

- **Automated tests:** `tests/test_local_script.py` covers CLI argument parsing
  and a mocked connect/download/complete round-trip.
- **Manual test steps:**
  1. Start `mock_core`: `uvicorn mock_core.main:app --port 9000`.
  2. Run `python -m local_script.septify_plugin --session-token sess_test list`.
  3. Run `connect example-document-organizer --session-token sess_test`.
  4. Run `download-url <file_id>`.
  5. Run `upload-url notice.pdf`.
  6. Run `complete <completion_token> provider_abc notice.pdf --size 1024`.

## Governance

- **Approval status:** `approved` as an internal reference plugin.
- **Code signing:** Not required for a local script; the tenant runs the source
  directly.
- **Update cadence / versioning policy:** Patch the `__version__` in
  `local_script/__init__.py` and the manifest version in `core/seeding.py` when
  the contract changes.

## Rollback

- **Token revocation:** The tenant can `DELETE /api/v1/plugins/tokens/{token_id}`
  from a session-authenticated client.
- **Disable / uninstall:** Delete `local_script/config.json` and remove the
  source directory. No server-side state is required.
